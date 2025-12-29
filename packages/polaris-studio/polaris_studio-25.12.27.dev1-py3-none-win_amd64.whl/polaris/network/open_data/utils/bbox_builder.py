# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from math import ceil, sqrt
from shapely.geometry import box


def build_bounding_boxes(model_boundaries, tile_size, transformer, model_zones_polygon):
    parts = ceil(sqrt(model_boundaries.area / (tile_size * tile_size * 1000 * 1000)))
    area_bounds = list(model_boundaries.bounds)
    area_bounds[1], area_bounds[0] = transformer.transform(area_bounds[0], area_bounds[1])
    area_bounds[3], area_bounds[2] = transformer.transform(area_bounds[2], area_bounds[3])
    if parts == 1:
        bboxes = [area_bounds]
    else:
        bboxes = []
        xmin, ymin, xmax, ymax = area_bounds
        ymin_global = ymin
        delta_x = (xmax - xmin) / parts
        delta_y = (ymax - ymin) / parts
        for _ in range(parts):
            xmax = xmin + delta_x
            for _ in range(parts):
                ymax = ymin + delta_y
                bbox = [xmin, ymin, xmax, ymax]
                if box(bbox[1], bbox[0], bbox[3], bbox[2]).intersects(model_zones_polygon):
                    bboxes.append(bbox)
                ymin = ymax
            xmin = xmax
            ymin = ymin_global
    return bboxes
