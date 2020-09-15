'''
Created on Sep 8, 2018

@author: rene
'''
from mayavi import mlab
from osgeo import ogr
import rasterio
from rtree import index
from shapely.geometry.geo import box
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

import numpy as np


def process(vector_path, height, width, transform, NODATA=None):

    # Spatial index to efficiently find triangles
    p = index.Property()
    idx = index.Index(properties=p, interleaved=True)

    polys = []

    def add_triangle(p1, p2, p3):

        # create plane from points
        # from http://kitchingroup.cheme.cmu.edu/blog/2015/01/18/Equation-of-a-plane-through-three-points/

        # convert to numpy vectors
        p1 = np.array([p1[0], p1[1], p1[2]])
        p2 = np.array([p2[0], p2[1], p2[2]])
        p3 = np.array([p3[0], p3[1], p3[2]])

        v1 = p3 - p1
        v2 = p2 - p1

        cp = np.cross(v1, v2)
        a, b, c = cp
        d = np.dot(cp, p3)

        # create 2d poly
        poly = Polygon([(p1[0], p1[1]),
                        (p2[0], p2[1]),
                        (p3[0], p3[1])])

        if poly.area >= 0:
            pid = len(polys)
            polys.append(poly)

            idx.insert(pid, poly.bounds, obj=(poly, (a, b, c, d)))

    # Read vector data only for selected rectangle
    xmin, ymin = (0, 0) * transform
    xmax, ymax = (width, height) * transform

    ds = ogr.Open(vector_path)
    layer = ds.GetLayer(0)
    layer.SetSpatialFilterRect(xmin, ymin, xmax, ymax)

    for feature in layer:
        geom = feature.GetGeometryRef()

        if geom.GetGeometryType() == ogr.wkbTINZ:
            for triangle in geom:
                for ring in triangle:
                    assert ring.GetPointCount() == 4
                    assert ring.GetPoint(0) == ring.GetPoint(3)
                    add_triangle(p1=ring.GetPoint(0),
                                 p2=ring.GetPoint(1),
                                 p3=ring.GetPoint(2))

        elif geom.GetGeometryName() == "MULTIPOLYGON":
            for poly in geom:
                for ring in poly:
                    # Check assumptions: each polygon is a triangle
                    assert ring.GetPointCount() == 4
                    assert ring.GetPoint(0) == ring.GetPoint(3)
                    add_triangle(p1=ring.GetPoint(0),
                                 p2=ring.GetPoint(1),
                                 p3=ring.GetPoint(2))
        else:
            print("?", geom.GetGeometryName(), feature.GetGeometryRef().ExportToWkt())

    # Interpolate

    res = np.zeros((width, height))

    for h in range(height):
        for w in range(width):

            x, y = (h + 0.5, w + 0.5) * transform

            _xmin, _ymin = (h, w) * transform
            _xmax, _ymax = (h + 1, w + 1) * transform
            _geom = box(_xmin, _ymin, _xmax, _ymax).centroid

            hits = idx.intersection(_geom.bounds, objects=True)

            z = float('-inf')

            # We select the highest z value for each triangle x,y intersects
            for hit in hits:
                if hit.object[0].intersects(_geom):

                    a, b, c, d = hit.object[1]
                    if not c == 0.0:
                        _z = (d - a * x - b * y) / c
                        z = max(_z, z)
                    else:
                        print(hits)

            if z == float('-inf'):
                z = NODATA
            res[w, h] = z

    return res


if __name__ == '__main__':

    with rasterio.open("rad_AV_1428373.tif") as src:
        print(src.meta)

        intpol = process(vector_path="musterdatenswissbuildings3d20lv03/LV03/SHP/Musterdaten_swissBUILDINGS3D20_LV03_1166_42.shp",
                         height=src.height,
                         width=src.width,
                         transform=src.transform,
                         NODATA=531.6)
        print(intpol)

        with rasterio.open("out.tif",
                           mode="w",
                           driver=src.driver,
                           height=src.height,
                           width=src.width,
                           crs=src.crs,
                           transform=src.transform,
                           count=1,
                           dtype=src.meta['dtype']) as dst:
            dst.write(intpol.astype(np.float32), 1)


