"""Dictionary References to Google Earth Engine Assets
"""

import ee
ee.Initialize()

iCol = {
    'dw': ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
}

fCol = {}
