'''
Created on Sep 8, 2018

@author: rene
'''
import csv
import datetime
from math import floor, ceil
import os

import fiona
import pyproj
import rasterio
from rasterio.crs import CRS
from rasterio.windows import Window
from shapely.geometry.geo import shape
from shapely.geometry.polygon import Polygon

import numpy as np
from datetime import date


cell_width_m = 0.5
helf_cell_width_m = cell_width_m * 0.5
cell_area = cell_width_m * cell_width_m

cmsaf_path = "/data_PV_Solar/cmsaf"

if __name__ == '__main__':
    with open(os.path.join("..", "data_PV_Solar", 'matching.csv')) as f:
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            bfsnr = row['GWR_gdenr']
            bid = row['bid']
            btype = row['btype']

            if not bid == "1085585":
                continue

            x = float(int(row['GWR_x']))
            y = float(int(row['GWR_y']))

            D = 100.0
            proj_lv03 = pyproj.Proj("+init=EPSG:21781")
            proj_lv95 = pyproj.Proj("+init=EPSG:2056")

            if row['GWR_gdekt'] in ("BL", "GE"):

                src = fiona.open('/home/rbuffat/buildings_av_osm_tlm_lv95.shp')
                _x, _y = pyproj.transform(proj_lv03, proj_lv95, x, y)
                bbox = (_x - D, _y - D, _x + D, _y + D)
                crs = CRS.from_epsg(2056)

            else:
                src = fiona.open('/home/rbuffat/buildings_av_osm_tlm.shp')
                bbox = (x - D, y - D, x + D, y + D)
                crs = CRS.from_epsg(21781)
                proj = pyproj.Proj("+init=EPSG:21781")

            geom = None
            for ss in src.filter(bbox=bbox):
                if ss['properties']['bid'] == int(row['bid']) and ss['properties']['btype'] == row['btype']:
                    geom = shape(ss['geometry'])

            # get building area
            barea = geom.area

            hor_sis = []
            # get hor solar irad
            lon, lat = pyproj.transform(proj_lv03, pyproj.Proj("+init=EPSG:4326"), x, y)
            d = datetime.date(2017, 1, 1)
            while d.year < 2018:
#                 logging.info("{}_{}: {}".format(btype, bid, str(d)))
                year = d.year
                month = d.month
                day = d.day

                fname = "SISin{year}{month:02d}{day:02d}0000003231000101UD.nc".format(year=year,
                                                                                      month=month,
                                                                                      day=day)

                src_sis = rasterio.open(os.path.join(cmsaf_path, "sis", fname))

                fwd_sis = src_sis.transform
                c_sis, r_sis = (lon, lat) * ~fwd_sis
                data_sis = src_sis.read(window=Window(int(c_sis), int(r_sis), 1, 1))

                dd = datetime.datetime(year, month, day)
                end_dd = datetime.datetime(year, month, day) + datetime.timedelta(days=1)

                i = 0
                while dd < end_dd:
                    # global rad hor
                    sis = float(max(data_sis[i, 0, 0], 0))
                    hor_sis.append(sis)
                    i += 1
                    dd += datetime.timedelta(minutes=30)
                d += datetime.timedelta(days=1)


            # read solar data_PV_Solar
            with rasterio.open(os.path.join("/data_PV_Solar","solarrad30min","rad30min_{}_{}.tif".format(btype, bid))) as rst:
                print("read data_PV_Solar")
                data = rst.read()
 
                print("aggregate")
                data_year = np.sum(data, axis=0)
 
                fwd = rst.transform
 
                bds = geom.bounds
                minx = floor(bds[0])
                miny = floor(bds[1])
                maxx = ceil(bds[2])
                maxy = ceil(bds[3])
 
                tot_rad = 0.0
                tot_rads = []

#                 c, r = ~fwd * (x, y)
#                 c = int(c)
#                 r = int(r)
# 
#                 i = 0
#                 d = datetime.datetime(2017, 1, 1, 0, 0)
#                 while(d.year < 2018):
# 
#                     print(hor_sis[i], rst.read(i + 1)[r, c])
#                     d += datetime.timedelta(minutes=30)
#                     i += 1

                print("extract data_PV_Solar")
                for x in np.arange(minx + helf_cell_width_m, maxx, cell_width_m):
                    for y in np.arange(miny + helf_cell_width_m, maxy, cell_width_m):
                        poly = Polygon([(x - helf_cell_width_m, y - helf_cell_width_m),
                                        (x - helf_cell_width_m, y + helf_cell_width_m),
                                        (x + helf_cell_width_m, y + helf_cell_width_m),
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

                        # Rad is in W/m2 for each cell and 30 min period (* 0.25) with cell area of 0.25
                        rad_y = data_year[r, c] * 0.5
                        print(rad_y, "W/m2")

                        tot_rad += data_year[r, c] * 0.5 * area
                print(tot_rad / barea)


