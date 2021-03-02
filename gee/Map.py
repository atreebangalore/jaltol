# -*- coding: utf-8 -*-
"""
functions to use GEE within Qgis python script
"""
import math
import ee

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsPointXY, QgsRectangle
from qgis.utils import iface

from . import utils
from . import ee_auth

# init the Google Earth Engine user authorization system
ee_auth.init()

def addLayer(eeObject, visParams=None, name=None, shown=True, opacity=1.0):
    """
        Adds a given EE object to the map as a layer.

        https://developers.google.com/earth-engine/api_docs#mapaddlayer

        Uses:
            >>> from ee_plugin import Map
            >>> Map.addLayer(.....)
    """
    print("In add Layer")
    utils.add_or_update_ee_layer(eeObject, visParams, name, shown, opacity)