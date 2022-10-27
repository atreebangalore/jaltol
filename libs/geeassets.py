"""Dictionary References to Google Earth Engine Assets
"""

import ee
ee.Initialize()

iCol = {
    'dw': ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1"),
    'refET': ee.ImageCollection('users/jaltol/ET_new/refCropET'),
}

fCol = {
    'dist2011' : ee.FeatureCollection('users/jaltol/FeatureCol/District_Map_2011'),
    'hydrosheds': ee.FeatureCollection('users/jaltol/FeatureCol/Hydroshds_Jaltol'),
}
