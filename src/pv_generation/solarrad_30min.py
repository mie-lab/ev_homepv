'''
Created on Sep 5, 2018

@author: rene
'''
from _collections import defaultdict
import copy
import csv
from datetime import date
import datetime
import logging
from multiprocessing import Pool
import multiprocessing
import os
import pprint
import shutil
import tempfile
import traceback

import csolar2.solar
import fiona
import pyproj
import rasterio
from rasterio.crs import CRS
from rasterio.features import rasterize
from rasterio.windows import Window
from shapely.geometry.geo import shape
from shapely.geometry.point import Point

import numpy as np


logging.basicConfig(filename='rad30min.log',
                    level=logging.INFO)

proj_84 = pyproj.Proj("+init=EPSG:4326")

base_path = "."
cmsaf_path = "/data/cmsaf"
outpath = "/data/solarrad30min"

NODATA = -9999.0


def transform_angle(angle):
    angle = (360.0 - angle) - 90.0
    if angle > 180.0:
        return -180.0 + (angle - 180.0)
    else:
        return angle


def process_building(geom, crs, proj, btype, bid):

    
#     geom, crs, proj = args

    ct = geom.centroid

    lon, lat = pyproj.transform(proj, proj_84, ct.x, ct.y)

    # open building data files
    try:

        hor5kpath = os.path.join(base_path, r"5khorizons")
        horpath = os.path.join(base_path, r"horizons")

        horfname = "{}_{}.tar.gz".format(btype, bid)
        building_path = os.path.join(horpath, horfname)

        if not os.path.exists(building_path):
            logging.info("{} no datafiles found for {}".format(str(datetime.datetime.now()),
                                                            building_path))
            return

        zipdirpath = tempfile.mkdtemp(prefix="/tmp/")
        shutil.unpack_archive(
            building_path,
            extract_dir=zipdirpath,
            format='gztar')

        # Load slope/aspect if not existing
        if not os.path.exists(os.path.join(zipdirpath, 'slope')):
            horfnamesa = "{}_{}sa.tar.gz".format(btype, bid)
            building_path2 = os.path.join(horpath, horfnamesa)
            shutil.unpack_archive(building_path2,
                                  extract_dir=zipdirpath,
                                  format='gztar')

        def read_data(ds):
            with rasterio.open(os.path.join(zipdirpath, ds)) as src:
                return src.read()[0], src.transform, not src.meta['transform'][0] == 0.5, src.meta

        slopes, fwd, bad, meta = read_data('slope')
        if bad:
            logging.info("BAD SLOPE")
            return
        aspects, fwd_a, bad, meta = read_data('aspect')
        if bad:
            logging.info("BAD ASPECT")
            return

        slopes[np.where(np.isnan(slopes))] = 99999
        aspects[np.where(np.isnan(aspects))] = 99999

        horizons = {}
        for az in range(-120, 121, 5):
            horizons[float(az)] = read_data("{}_{}_{}".format(btype,
                                                              bid,
                                                              az))[0]

        horizons2 = defaultdict(lambda: 0.0)
        hor5kfname = "{}_{}_hor.txt".format(btype, bid)
        hor2_path = os.path.join(hor5kpath, hor5kfname)
        with open(hor2_path, mode='r') as ff:
            for line in ff:
                vals = list(
                    map(float, line.strip().split(';')))
                horizons2[vals[0]] = vals[1]

#         pprint.pprint(horizons2)

#         logging.info("{} read {}_{}s".format(str(datetime.datetime.now()),
#                                              btype,
#                                              bid))
        # PROCESS

        h, w = slopes.shape

        geom2 = geom.buffer(6.0)
        buildingmap = rasterize([(geom2, 1)],
                                out_shape=(h, w),
                                fill=0,
                                all_touched=True,
                                transform=fwd,
                                dtype=rasterio.uint8)

        # get 30min of year (we could optimize this)
        t = 0
        d = datetime.datetime(2017, 1, 1, 0, 0)
        while d.year == 2017:
            t += 1
            d += datetime.timedelta(minutes=30)


        # Create output file
        fpath = os.path.join(outpath, "rad30min_{}_{}.tif".format(btype, bid))
        with rasterio.open(fpath,
                           mode='w',
                           driver="GTiff",
                           width=w,
                           height=h,
                           count=t,
                           transform=fwd,
                           crs=crs,
                           nodata=NODATA,
                           dtype='float32') as dst:


            # Iterate over all radiation data, each file contains the 30 minutes values of one day
            d = datetime.date(2017, 1, 1)
            b = 0
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

                fname = "SIDin{year}{month:02d}{day:02d}0000003231000101UD.nc".format(year=year,
                                                                                      month=month,
                                                                                      day=day)

                src_sid = rasterio.open(os.path.join(cmsaf_path, "sid", fname))

                fwd_sid = src_sid.transform
                c_sid, r_sid = (lon, lat) * ~fwd_sid
                data_sid = src_sid.read(window=Window(int(c_sid), int(r_sid), 1, 1))

                # Each nc file contains the 30 minute periods of a day as band
                # We iterate over each band
                dd = datetime.datetime(year, month, day)
                end_dd = datetime.datetime(year, month, day) + datetime.timedelta(days=1)

                i = 0
                while dd < end_dd:

                    rad = np.zeros((h, w))

                    # Solar irradiation config for spa.c algorithm
                    s = csolar2.solar.Solar(
                        lat,
                        lon,
                        dd,
                        0,
                        elevation=600,
                        temperature=11,
                        pressure=1020)

                    # global rad hor
                    sis = float(max(data_sis[i, 0, 0], 0))

                    # direct rad hor
                    sid = float(max(data_sid[i, 0, 0], 0))

                    # Iterate over all cells
                    for _h in range(h):
                        for _w in range(w):

                            _rad = 0.0
                            if slopes[_h, _w] < 99999 and aspects[_h, _w] < 99999:
                                # slope 
                                beta_deg = slopes[_h, _w]

                                # azimuth
                                alpha_deg = transform_angle(aspects[_h, _w])

                                # transform alpha

                                # direct rad dif
                                dif = sis - sid
                                assert dif >= 0.0


                                dir_tilted, dif_tilted, sis_tilted = csolar2.solar.get_tilted_rad(s,
                                                                                                  sis,
                                                                                                  sid,
                                                                                                  0.2,
                                                                                                  beta_deg,
                                                                                                  alpha_deg)

                                sun_elevation = s.get_elevation_angle()
                                sun_azimuth = round(s.get_azimuth() / 5.0) * 5.0

                                # We do nothing if we have no irradiation
                                if sis_tilted >= 0.0 and sun_elevation >= 0.0 and sun_azimuth >= -120 and sun_azimuth <= 120.0:

                                    h1 = horizons[sun_azimuth][_h, _w]
                                    h2 = horizons2[sun_azimuth]
                                    max_hor = max(h1, h2)

                                    if max_hor < sun_elevation:
                                        _rad = dir_tilted + dif_tilted
                                    else:
                                        _rad = dif_tilted

                            rad[_h, _w] = _rad
                    dst.write(rad.astype(np.float32), b + 1)
                    dd += datetime.timedelta(minutes=30)
                    i += 1
                    b += 1

                src_sis.close()
                src_sid.close()

                d += datetime.timedelta(days=1)

    except Exception as e:
        logging.error("{}: ERROR: {} \n {}".format(str(datetime.datetime.now()),
                                               str(e),
                                               traceback.format_exc()))


if __name__ == '__main__':

    jobs = []
    print("create jobs")
    with open(os.path.join("..", "data", 'matching.csv')) as f:
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            bfsnr = row['GWR_gdenr']
            bid = row['bid']
            btype = row['btype']

#             if not bid == "1401484":
#                 continue

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
                pass

            else:
                src = fiona.open('/home/rbuffat/buildings_av_osm_tlm.shp')
                bbox = (x - D, y - D, x + D, y + D)
                crs = CRS.from_epsg(21781)
                proj = pyproj.Proj("+init=EPSG:21781")

            geom = None
            for ss in src.filter(bbox=bbox):
                if ss['properties']['bid'] == int(row['bid']) and ss['properties']['btype'] == row['btype']:
                    geom = shape(ss['geometry'])

            jobs.append((geom, crs, proj, btype, bid))

    print("process jobs")
    with Pool(multiprocessing.cpu_count()) as p:
        p.starmap(process_building, jobs)
    print("done")

