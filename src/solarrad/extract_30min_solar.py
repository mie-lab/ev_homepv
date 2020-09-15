'''
Created on Aug 29, 2018

@author: rene
'''
from _collections import defaultdict
import csv
import json
from math import floor, ceil
import os
import pprint

import fiona
import pyproj
import rasterio
from shapely.geometry.geo import shape
from shapely.geometry.polygon import Polygon

import numpy as np


cell_width_m = 0.5
helf_cell_width_m = cell_width_m * 0.5
cell_area = cell_width_m * cell_width_m
percentiles = sorted(
    list(np.arange(0, 105, 5)) + [1.0, 2.5, 33.3, 66.6, 97.5, 99.0])

rad_cat_size = 50000.0

D = 100.0
proj_lv03 = pyproj.Proj("+init=EPSG:21781")
proj_lv95 = pyproj.Proj("+init=EPSG:2056")

if __name__ == '__main__':
    with open('matching.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            bfsnr = row['GWR_gdenr']
            bid = row['bid']
            btype = row['btype']

            print(btype, bid)

            x = float(int(row['GWR_x']))
            y = float(int(row['GWR_y']))

            if row['GWR_gdekt'] in ("BL", "GE"):
                continue
                src = fiona.open('/home/rene/output/buildings/buildings_av_osm_tlm_lv95.shp')
                _x, _y = pyproj.transform(proj_lv03, proj_lv95, x, y)
                bbox = (_x - D, _y - D, _x + D, _y + D)

            else:
                src = fiona.open('/home/rene/output/buildings/buildings_av_osm_tlm.shp')
                bbox = (x - D, y - D, x + D, y + D)

            geom = None
            for ss in src.filter(bbox=bbox):
                if ss['properties']['bid'] == int(row['bid']) and ss['properties']['btype'] == row['btype']:
                    geom = shape(ss['geometry'])

            bpath = os.path.join("solarout", "rad30min_{}_{}.tif".format(btype, bid))

            if os.path.exists(bpath):

                """
                    List with radiation kwh
                """
                radiation_Wh_tots = defaultdict(float)
                tot_rad = 0.0

                with rasterio.open(bpath) as rst:
                    """
                        Each cell contains the monthly producable kwh/m2. As cell is only 0.5 * 0.5 meter,
                        we have to correct by multiplying with 0.5*0.5
                    """
                    data = rst.read()

                    data_year = np.sum(data, axis=0)

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

                            t = 0

                            try:
                                rad_y = data_year[r, c]
                                rad_cat = int(round(rad_y / rad_cat_size) * rad_cat_size)
                            except Exception as e:
                                print(row['GWR_gdekt'])
                                print(r, c, data_year.shape, data.shape)
                                print(str(e))
                                a = 5 / 0

                            for month in range(1, 13):
                                for hour in range(0, 24):
                                    for minute in range(0, 31, 30):

                                        T = int((month - 1) * 24 * 2 + hour * 2 + minute / 30)
                                        # w / m2 * m2
                                        rad = data[T, r, c] * area

                                        radiation_Wh_tots[(month, hour, minute, rad_cat)] += rad
                                        tot_rad += rad

                def conv(dd):
                    newdd = {}
                    for k in dd.keys():
                        kk = "_".join(list(map(str, k)))
                        try:
                            newdd[kk] = float(dd[k])
                        except Exception as e:
                            print(str(e))
                            newdd[kk] = None
                    return newdd

                print(tot_rad)

                with open(os.path.join("solarrad", "{}_{}.json".format(btype, bid)), "w") as f:
                    json.dump(conv(radiation_Wh_tots), f, indent=4)


