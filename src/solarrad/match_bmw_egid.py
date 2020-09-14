'''
Created on Aug 14, 2018

@author: rene
'''
from _collections import defaultdict
import csv
from math import floor, ceil
import os
import pprint

import fiona
import psycopg2
import psycopg2.extras
import pyproj
import rasterio
from shapely.geometry.geo import shape
from shapely.geometry.polygon import Polygon
import simplejson

import numpy as np
from pyxdameraulevenshtein import damerau_levenshtein_distance

proj_lv03 = pyproj.Proj("+init=EPSG:21781")
proj_lv95 = pyproj.Proj("+init=EPSG:2056")

radkeys = ['avg', 'min', '25', '75', 'max']
selected_keys = ['avg', '25', '75']

selected_idx = [radkeys.index(k) for k in selected_keys]

cell_width_m = 0.5
helf_cell_width_m = cell_width_m * 0.5
cell_area = cell_width_m * cell_width_m
percentiles = sorted(
    list(np.arange(0, 105, 5)) + [1.0, 2.5, 33.3, 66.6, 97.5, 99.0])

rad_cat_size = 50000.0

if __name__ == '__main__':

    dbstring = "host=ikgpgis2.ethz.ch port=5432 dbname=postgres user=ifu  connect_timeout=2 password='lass_mich_auf_die_gebaeude_daten_zugreifen'"


    conn = psycopg2.connect(dbstring)
    dbc = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    with open("matching.csv", 'w') as ff:

        headers = ["BMW_vid", "BMW_userid", "BMW_street", "BMW_PLZ", "BMW_Ort", "GWR_EGID", "GWR_gdekt", "GWR_gdenr", "GWR_strnamk1", "GWR_nr", "GWR_plz4", "GWR_x", "GWR_y", "GWR_gbaup", "GWR_gbauj", "GWR_gkat", "damerau_levenshtein_distance", "btype", "bid", "solar"]
#         for k in selected_keys:
#             for m in range(13):
#                 for rad_cat in range(0, 2000000, 50000):
#                     headers.append("{}_{}_{}Wh".format(k, m, rad_cat))

        ff.write(";".join(list(map(str, headers))) + "\n")

        with open(os.path.join("..", "data", "ids_address.csv"), encoding="iso-8859-15") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if len(row['Kontrollschild-Nr']) > 0:
                    vid = row['vid']
                    userid = row['userid']
                    street = row['Strasse'].lower()
                    plzo = row['PLZ']
                    city = row['Ort']

                    # Get street nr
                    nr = None
                    nrs = [s for s in street.split() if any(c.isdigit() for c in s)]
                    if len(nrs) > 0:
                        nr = nrs[0].lower()
                    else:
                        print(street, nrs)

                    sql = "select gdekt, gkat, egid, strnamk1, gdenr, deinr, gkodx, gkody,gbaup,gbauj, plz4 from heat.gwr_geb_20170601 where plz4 = {}".format(plzo)
                    dbc.execute(sql)
                    entries = []
                    for r in dbc:
                        sqlstreet = "{} {}".format(r['strnamk1'], r['deinr']).lower()
                        entries.append((sqlstreet, damerau_levenshtein_distance(street, sqlstreet), dict(r)))

                    # Sort according in ascending levenshtein distance
                    entries.sort(key=lambda x: x[1])
                    selected = None
                    # If we have a address with no streetnr
                    if nr is None:
                        selected = (entries[0][2], None)

                    # Select first entry with same streetnr
                    else:
                        for e in entries:
                            if nr in e[0]:
                                selected = (e[2], e[1])
                                break
#                     if selected is not None:
#                         print(street, "|" "{} {}".format(selected['strnamk1'], selected['deinr']), "|", selected)
#                     else:
#                         print(street, "NOT FOUND")

                    d = defaultdict(lambda: None)
                    d['BMW_vid'] = vid
                    d['BMW_userid'] = userid
                    d['BMW_street'] = street
                    d['BMW_PLZ'] = plzo
                    d['BMW_Ort'] = city

                    if selected is not None:
                        d['GWR_EGID'] = selected[0]['egid']
                        d['GWR_gdekt'] = selected[0]['gdekt']
                        d['GWR_gdenr'] = selected[0]['gdenr']
                        d['GWR_strnamk1'] = selected[0]['strnamk1']
                        d['GWR_nr'] = selected[0]['deinr']
                        d['GWR_plz4'] = selected[0]['plz4']
                        d['GWR_x'] = selected[0]['gkodx']
                        d['GWR_y'] = selected[0]['gkody']
                        d['GWR_gbaup'] = selected[0]['gbaup']
                        d['GWR_gbauj'] = selected[0]['gbauj']
                        d['GWR_gkat'] = selected[0]['gkat']
                        d['damerau_levenshtein_distance'] = selected[1]

                        # get building
                        sql = "select bid,btype from heat.gwrmatches2 as gm, heat.gwr as g where g.gwrid = gm.gwrid and g.egid = {}".format(selected[0]['egid'])
                        dbc.execute(sql)
                        for r in dbc:
                            d['bid'] = r['bid']
                            d['btype'] = r['btype']

                        # get solar data
                        if d['bid'] is not None and d['btype'] is not None:
                            geom = None

                            D = 100.0
                            if d['GWR_gdekt'] in ("BL", "GE"):
                                src = fiona.open('/home/rene/output/buildings/buildings_av_osm_tlm_lv95.shp')
                                x, y = pyproj.transform(proj_lv03, proj_lv95, d['GWR_x'], d['GWR_y'])
                                print(x,y)

                                bbox = (x - D, y - D, x + D, y + D)
                            else:
                                src = fiona.open('/home/rene/output/buildings/buildings_av_osm_tlm.shp')
                                bbox = (d['GWR_x'] - D, d['GWR_y'] - D, d['GWR_x'] + D, d['GWR_y'] + D)
                            for ss in src.filter(
                                    bbox=bbox):
                                if ss['properties']['bid'] == d['bid'] and ss['properties']['btype'] == d['btype']:
                                    geom = shape(ss['geometry'])
                            src.close()

                            # Get solar irrad
                            bpath = os.path.join("data", "solar",
                                                 "rad_{}_{}.tif".format(d['btype'], d['bid']))

                            if os.path.exists(bpath):

                                """
                                    List with radiation kwh
                                """
                                radiation_Wh_area = defaultdict(float)
                                radiation_Wh_tots = defaultdict(float)

                                with rasterio.open(bpath) as rst:
                                    """
                                        Each cell contains the monthly producable kwh/m2. As cell is only 0.5 * 0.5 meter,
                                        we have to correct by multiplying with 0.5*0.5
                                    """
                                    data = rst.read()
                                    fwd = rst.transform
 
                                    bds = geom.bounds
                                    minx = floor(bds[0])
                                    miny = floor(bds[1])
                                    maxx = ceil(bds[2])
                                    maxy = ceil(bds[3])
 
                                    for x in np.arange(
                                            minx + helf_cell_width_m, maxx, cell_width_m):
                                        for y in np.arange(
                                                miny + helf_cell_width_m, maxy, cell_width_m):
 
                                            poly = Polygon([(x - helf_cell_width_m, y - helf_cell_width_m),
                                                            (x -
                                                             helf_cell_width_m, y +
                                                             helf_cell_width_m),
                                                            (x +
                                                             helf_cell_width_m, y +
                                                             helf_cell_width_m),
                                                            (x + helf_cell_width_m, y - helf_cell_width_m)])
 
                                            if not poly.intersects(geom):
                                                continue
 
                                            area = geom.intersection(poly).area
 
                                            in_r = area / cell_area
 
                                            if in_r == 0.0:
                                                continue
 
                                            c, r = ~fwd * (x, y)
                                            c = int(c)
                                            r = int(r)
 
                                            for ii, k in enumerate(selected_keys):
                                                i = selected_idx[ii]
                                                n = 13 * i + 0
                                                rad = data[n, r, c]
                                                rad_cat = int(round(rad / rad_cat_size) * rad_cat_size)
 
                                                for m in range(13):
                                                    n = 13 * i + m
 
                                                    rad = data[n, r, c]
                                                    radiation_Wh_tots[(k, m, rad_cat)] += rad * area
                                                    radiation_Wh_area[(k, m, rad_cat)] += area
 
                                def conv(dd):
                                    newdd = {}
                                    for k in dd.keys():
                                        kk = "_".join(list(map(str, k)))
                                        try:
                                            newdd[kk] = float(dd[k])
                                        except:
                                            newdd[kk] = None
                                    return newdd

                                d['solar'] = simplejson.dumps(conv(radiation_Wh_tots))

#                                 for k in selected_keys:
#                                     for m in range(13):
#                                         for rad_cat in range(0, 2000000, 50000):
#                                             d["{}_{}_{}Wh".format(k, m, rad_cat)] = radiation_Wh_tots[(k, m, rad_cat)]

                    if d['solar'] is not None:
                        line = (";".join(list(map(str, [d[k] for k in headers])))) + "\n"
                        print(line)
                        ff.write(line)



