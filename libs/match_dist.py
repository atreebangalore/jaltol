"""for input ee.Feature match with the 2011 district map and 
return the state name and district name so as to prevent matching 
district name errors

Returns:
    Tuple[str]: State Name and District Name from 2011 District map
"""
import ee
ee.Initialize()
from .geeassets import fCol

def get_admin_info(feature):
    geom = ee.Feature(feature)
    geometry_centroid = geom.centroid()
    dist_boundary = fCol['dist2011']
    filtered = dist_boundary.filterBounds(geom.geometry())
    def calc_dist(poly):
        dist = geometry_centroid.distance(poly.centroid())
        return poly.set('mindist',dist)
    dist_fc = filtered.map(calc_dist)
    min_dist = dist_fc.sort('mindist', True).first().getInfo()
    return (min_dist['properties']['ST_NM'], min_dist['properties']['DISTRICT'])