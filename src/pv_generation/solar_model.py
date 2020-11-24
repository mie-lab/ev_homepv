'''
Created on Aug 28, 2018

@author: rene
'''
import pprint


test_path = r"SISin201312312330-CH.nc"


def create_idx(x, y):
    import pyproj
    import rasterio
    proj_lv03 = pyproj.Proj("+init=EPSG:21781")
    proj_ms = pyproj.Proj("+init=EPSG:4326")

    lon, lat = pyproj.transform(
        proj_lv03,
        proj_ms,
        x,
        y)

    with rasterio.open(test_path) as src:
        fwd_sis = ~src.transform
        c, r = fwd_sis * (lon, lat)
        r = int(r) + 0.5
        c = int(c) + 0.5

        lon, lat = src.transform * (c, r)
    lon = round(lon, 3)
    lat = round(lat, 3)

    return (r, c, lat, lon)


def read_radmap(args, base_path, fff):
    import numpy as np
    import os
    import rasterio
    from math import floor, ceil
    import umsgpack
    from scipy.interpolate.fitpack2 import RectBivariateSpline
    from collections import defaultdict
    import datetime
    import scipy.stats as stats

    rad_basedir = os.path.join(base_path, r'quantile_maps', r'quantile_maps_monthly')
#     rad_basedir_year = os.path.join(base_path, r'quantile_maps', r'quantile_maps_monthly_allyears')

    h, w, lat, lon, bbox84, base_paths, outdir = args

    days = [
        31.0,
        28.0,
        31.0,
        30.0,
        31.0,
        30.0,
        31.0,
        31.0,
        30.0,
        31.0,
        30.0,
        31.0]

    alpha_degs = np.arange(-180.0, 181.0, 15.0)
    beta_degs = np.arange(0.0, 95.0, 10.0)

    rad_inp = defaultdict(dict)
    rad_inp_rst = defaultdict(dict)

#     for radkey in['avg', 'min', '25', '75', 'max']:
    for radkey in['avg']:
        for radtype in ['sis', 'dif', 'dir']:
            rad_inp_rst[(radkey, radtype)] = np.zeros((12, 38, 91, 361), dtype=np.uint16)

    for month in range(1, 13):
#     for month in range(1, 2):

        fff.write(
            "{} interpolate radiation month {}".format(str(datetime.datetime.now()),
                                                       month))
        fff.write("\n")
        fff.flush()

        inparas = ['rad', 'h', int(h), 'w', int(w), 'lat', lat, 'lon', lon, 'month', month]
        in_filename = "_".join(list(map(str, inparas))) + ".mp"
        in_path = os.path.join(rad_basedir, in_filename)

        with open(in_path, 'rb') as f:
            data_avg = umsgpack.load(f)

        for hour in range(3, 22):
            for mins in [0, 30]:
                hkey = (hour, mins)

                z_sis = np.zeros((len(beta_degs), len(alpha_degs)))
                z_dif = np.zeros((len(beta_degs), len(alpha_degs)))
                z_dir = np.zeros((len(beta_degs), len(alpha_degs)))

                for i, beta_deg in enumerate(beta_degs):
                    for j, alpha_deg in enumerate(alpha_degs):

                        akey = (alpha_deg, beta_deg)

                        z_sis[i, j] = float(data_avg[hkey][akey]['sis']['avg']) * days[month - 1] * 0.5
                        z_dif[i, j] = float(data_avg[hkey][akey]['dif']['avg']) * days[month - 1] * 0.5
                        z_dir[i, j] = float(data_avg[hkey][akey]['sid']['avg']) * days[month - 1] * 0.5

                rad_inp[('avg', 'sis', month)][hkey] = RectBivariateSpline(beta_degs, alpha_degs, z_sis)
                rad_inp[('avg', 'dif', month)][hkey] = RectBivariateSpline(beta_degs, alpha_degs, z_dif)
                rad_inp[('avg', 'dir', month)][hkey] = RectBivariateSpline(beta_degs, alpha_degs, z_dir)
        del hour, mins, hkey, i, j, beta_deg, alpha_deg

        for radkey in['avg']:

#         for radkey in['avg', 'min', '25', '75', 'max']:
            for radtype in ['sis', 'dif', 'dir']:
                for hour in range(3, 22):
                    for mins in [0, 30]:
                        hkey = (hour, mins)

                        RBS = rad_inp[(radkey, radtype, month)][hkey]
                        interpolated = RBS(np.arange(0, 91, 1), np.arange(-180, 181, 1), grid=True).astype(np.float32)
                        interpolated[interpolated < 0] = 0

                        mmax = np.max(interpolated)
                        if mmax > 65535:
                            fff.write(
                                "{}: Overflow : {} / {} {} {} {} ".format(str(datetime.datetime.now()),
                                                                          mmax,
                                                                          radkey,
                                                                          radtype,
                                                                          hour,
                                                                          mins
                                                                          )
                            )
                            fff.write("\n")
                            fff.flush()
                        t = int(hour * 2 + mins / 30) - 6
                        rad_inp_rst[(radkey, radtype)][month - 1, t, :, :] = interpolated.astype(np.uint16)

    mmax = 0.0
    mmin = 100000000
    for k in rad_inp_rst:
        fff.write(
            "{}: Max/min rad for {}: {}/{}".format(str(datetime.datetime.now()),
                                                   k,
                                                   np.max(rad_inp_rst[k]),
                                                   np.min(rad_inp_rst[k]))
                )
        fff.write("\n")
        mmax = max(mmax, np.max(rad_inp_rst[k]))
        mmin = min(mmin, np.min(rad_inp_rst[k]))

    fff.write(
        "{}: Max/min rad overall: {}/{}".format(str(datetime.datetime.now()),
                                                mmax,
                                                mmin)
    )
    fff.write("\n")
    fff.flush()

    return rad_inp_rst


def calc_profiles(lat, lon, fff):
    import copy
    import datetime
    import csolar2.solar
    import numpy as np

    avg_ns = [17.0,
              47.0,
              75.0,
              105.0,
              135.0,
              162.0,
              198.0,
              228.0,
              258.0,
              288.0,
              318.0,
              344.0]

    avg_days = [
        datetime.datetime(2015, 1, 1) +
        datetime.timedelta(days=n - 1) for n in avg_ns]

    elevations = np.ones((13, 38), dtype=np.float32) * -9999.0
    azimuths = np.ones((13, 38), dtype=np.float32) * -9999.0

    for month in range(1, 13):
        when = copy.copy(avg_days[month - 1]) + datetime.timedelta(hours=3)
        for hour in range(3, 22):
            for minute in [0, 30]:
                tt = int((hour * 2 + minute / 30) - 6)

                when += datetime.timedelta(minutes=30)
                s = csolar2.solar.Solar(
                    lat,
                    lon,
                    when,
                    0,
                    elevation=600,
                    temperature=11,
                    pressure=1020)
                elevations[month - 1, tt] = s.get_elevation_angle()
                azimuths[month - 1, tt] = round(s.get_azimuth() / 5.0) * 5.0
                fff.write(
                    "{}: {} - {}:{} / {} Elevation:  {}, Azimuth: {}".format(str(datetime.datetime.now()),
                                                                             month,
                                                                             hour,
                                                                             minute,
                                                                             tt,
                                                                             elevations[month - 1, tt],
                                                                             azimuths[month - 1, tt])
                )
                fff.write("\n")
    fff.flush()
    return elevations, azimuths


def process_building(base_path, geom, bfsnr, bid, btype, arg, radkeys, fff, crs):
    import os
    import datetime
    import time
    import tempfile
    import shutil
    import rasterio
    import numpy as np
    from collections import defaultdict
    import giesolarc.radcalc3
    from rasterio.features import rasterize
    import traceback

    NODATA = -9999

    try:

        elevations, azimuths = calc_profiles(lat, lon, fff)
        rad_inp = read_radmap(arg, base_path, fff)

        hor5kpath = os.path.join(base_path, r"5khorizons")
        horpath = os.path.join(base_path, r"horizons")

        horfname = "{}_{}.tar.gz".format(btype, bid)
        building_path = os.path.join(horpath, horfname)

        if not os.path.exists(building_path):
            fff.write("{} no datafiles found for {}".format(str(datetime.datetime.now()),
                                                            building_path))
            fff.write("\n")
            fff.flush()
            return


        # READ
        readts = time.time()

        ts = time.time()
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
            fff.write("BAD SLOPE")
            return
        aspects, fwd_a, bad, meta = read_data('aspect')
        if bad:
            fff.write("BAD ASPECT")
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

        fff.write("{} read {}_{}, took {} seconds".format(str(datetime.datetime.now()),
                                                          btype,
                                                          bid,
                                                          round(time.time() - readts, 2)))
        fff.write("\n")
        fff.flush()
        # PROCESS
        processts = time.time()

        h, w = slopes.shape

        geom2 = geom.buffer(6.0)
        buildingmap = rasterize([(geom2, 1)],
                                out_shape=(h, w),
                                fill=0,
                                all_touched=True,
                                transform=fwd,
                                dtype=rasterio.uint8)

        if not slopes.shape == aspects.shape:
            fff.write("{} {}_{}: WARNING: Slope and aspect have not same size: {} /  {}".format(str(datetime.datetime.now()),
                                                                                                   btype,
                                                                                                   bid,
                                                                                                   slopes.shape,
                                                                                                   aspects.shape))
            fff.write("\n")
            fff.flush()

        npradmaps, npradmaps_shadow = giesolarc.radcalc3.process(h,
                                                                 w,
                                                                 radkeys,
                                                                 elevations,
                                                                 azimuths,
                                                                 slopes,
                                                                 aspects,
                                                                 rad_inp,
                                                                 horizons,
                                                                 horizons2,
                                                                 buildingmap)

        fff.write("{} process {}_{}, took {} seconds".format(str(datetime.datetime.now()),
                                                             btype,
                                                             bid,
                                                             round(time.time() - processts, 2)))
        fff.write("\n")
        fff.flush()

        # WRITE
        writets = time.time()

        outpath = "solarout/rad30min_{}_{}.tif".format(btype, bid)
        with rasterio.open(outpath,
                           driver="GTiff",
                           mode='w',
                           width=meta['width'],
                           height=meta['height'],
                           count=12 * 24 * 2 * len(radkeys),
                           nodata=NODATA,
                           crs=crs,
                           transform=meta['transform'],
                           compress='lzw',
                           dtype=np.float32) as dst:

            dst.write(npradmaps,
                      indexes=range(1, 12 * 24 * 2 * len(radkeys) + 1))

        fff.write("{} write {}_{}, took {} seconds".format(str(datetime.datetime.now()),
                                                           btype,
                                                           bid,
                                                           round(time.time() - writets, 2)))
        fff.write("\n")
        fff.flush()

        shutil.rmtree(zipdirpath)
        ti = time.time() - ts
        fff.write("{} finished {}_{}, took {} seconds".format(str(datetime.datetime.now()),
                                                              btype,
                                                              bid,
                                                              round(ti, 2)))
        fff.write("\n")
        fff.flush()

    except Exception as e:
        print(str(e))
        fff.write("{}: ERROR: {} \n {}".format(str(datetime.datetime.now()),
                                               str(e),
                                               traceback.format_exc()))
        fff.write("\n")
        fff.flush()
        a = 5 / 0


if __name__ == '__main__':
    import csv
    import fiona
    import pyproj
    from rasterio.crs import CRS
    from shapely.geometry.geo import shape

    D = 100.0
    proj_lv03 = pyproj.Proj("+init=EPSG:21781")
    proj_lv95 = pyproj.Proj("+init=EPSG:2056")

    with open("/tmp/log.txt", 'w') as fff:

        with open('matching.csv') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                bfsnr = row['GWR_gdenr']
                bid = row['bid']
                btype = row['btype']

                x = float(int(row['GWR_x']))
                y = float(int(row['GWR_y']))
                r, c, lat, lon = create_idx(x, y)

                arg = (r, c, lat, lon, None, None, None)

                if row['GWR_gdekt'] in ("BL", "GE"):
                    src = fiona.open('/home/rene/output/buildings/buildings_av_osm_tlm_lv95.shp')
                    _x, _y = pyproj.transform(proj_lv03, proj_lv95, x, y)
                    bbox = (_x - D, _y - D, _x + D, _y + D)
                    crs = CRS.from_epsg(2056)

                else:
                    src = fiona.open('/home/rene/output/buildings/buildings_av_osm_tlm.shp')
                    bbox = (x - D, y - D, x + D, y + D)
                    crs = CRS.from_epsg(21781)

                geom = None
                for ss in src.filter(bbox=bbox):
                    if ss['properties']['bid'] == int(row['bid']) and ss['properties']['btype'] == row['btype']:
                        geom = shape(ss['geometry'])

                print(geom)

                process_building(".", geom, bfsnr, bid, btype, arg, ['avg'], fff, crs)





