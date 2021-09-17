import os
import ee
#import numpy as np
#import pandas as pd
#import matplotlib.pyplot as plt
#from matplotlib.figure import Figure
#from matplotlib import axes
from pathlib import Path
import sys
import time
import json
import inspect
import qgis.core
from qgis.core import (
  Qgis,
  QgsProject,
  QgsLayout,
  QgsLayoutExporter,
  QgsReadWriteContext,
  QgsVectorLayer,
  QgsFeature,
  QgsFeatureRequest,
  QgsExpression,
  QgsWkbTypes
  )
from qgis.gui import *

from PyQt5.QtWidgets import QAction, QFileDialog, QDockWidget,QMenu
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5.QtCore import Qt,QSignalMapper     #contains Qt.BrushStyle
from PyQt5.QtXml import QDomDocument

from datetime import datetime
from .ruralwater_dialog import RuralWaterDockWidget
import ee
from ee_plugin import Map
#from vectors import getLocalBoundaries

#print(dir(getLocalBoundaries))   # functions within module aren't registering.. dunno why

print(ee.String('Hello World from EE!').getInfo())
inspect_getfile = inspect.getfile(inspect.currentframe())
cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
home_dir = os.path.join(os.path.expanduser('~'))

class RuralWaterClass:
    def __init__(self, iface):                                          # give plugin class access to QgisInterface
        self.iface = iface

    def initGui(self):
      icon = os.path.join(os.path.join(cmd_folder, 'logo.png'))         # make path for logo image      
      self.action = QAction(QIcon(icon), '&Jaltol', self.iface.mainWindow())    # create QAction
      self.action.triggered.connect(self.run)                           # if QAction triggered, run
      self.iface.addPluginToMenu('&Jaltol', self.action)       # add action to menu
      self.iface.addToolBarIcon(self.action)
      self.first_start = True

    def unload(self):
      self.iface.removeToolBarIcon(self.action)                         # remove action from tool bar
      self.iface.removePluginMenu('&Jaltol', self.action)      # remove action from plugin menu
      del self.action

    ##########################################################################
    ##                            AOI                                       ##
    ##########################################################################

    def select_output_file(self,index):
      if index==0:
        print("index is 0")
        print("called select file for villages")
        self.dlg.lineE = self.dlg.lineEdit_aoi_selectVB
      elif index==1:
        print("index is 1")
        print("called select file for watersheds")
        self.dlg.lineE = self.dlg.lineEdit_aoi_selectWB
      elif index==2:
        print("index is 2")
        print("called select file for custom boundaries")
        self.dlg.lineE = self.dlg.lineEdit_aoi_selectCB
      else:
        pass
      filename, _filter = QFileDialog.getOpenFileName(                  # use file dialog to get filename 
            self.dlg, "Select shape file ","", '*.shp')
      self.dlg.lineE.setText(filename)
      print("line Edit populated")
      #self.add_boundary_layer()

      
    def add_boundary_layer(self,index):
      print("called add_boundary_layer")
      self.filename = self.dlg.lineE.text()
      if len(self.filename)==0:
        self.iface.messageBar().pushMessage('Please select the correct shapefile', level=Qgis.Critical, duration=10)
        return

      if index==0:
        self.layername = 'Village Boundaries'
        self.vlayer = QgsVectorLayer(self.filename, self.layername, "ogr")
      elif index==1:
        self.layername = 'Watershed Boundaries'
      elif index==2:
        self.layername = 'Custom Boundaries'
      else:
        pass

      print("layer name: ", self.layername)
      self.newlayer = QgsVectorLayer(self.filename, self.layername, "ogr")
      self.project.addMapLayer(self.newlayer)
      
      alayer = self.iface.activeLayer()
      single_symbol_renderer = alayer.renderer()
      symbol = single_symbol_renderer.symbol()
      symbol.symbolLayer(0).setBrushStyle(Qt.BrushStyle(Qt.NoBrush))
      
      if index==0:
        self.get_states()
      else:
        pass
      
    def get_states(self):
      print("called get States")
      idx = self.vlayer.fields().indexOf('State_N')
      li = sorted(self.vlayer.uniqueValues(idx))
      if qgis.core.NULL in li:
          li.remove(qgis.core.NULL)
      self.dlg.comboBox_aoi_selectS.clear()
      self.dlg.comboBox_aoi_selectS.addItems(li)

    def get_districts(self):
      print("called get Districts")
      self.state = self.dlg.comboBox_aoi_selectS.currentText()
      self.stateFilter = "\"State_N\"='" + self.state + "'"
      self.vlayerFilter = self.stateFilter
      #print(self.vlayerFilter)
      expr = QgsExpression(self.vlayerFilter)
      stateFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      print(stateFeas)

      li = []
      for fea in stateFeas:
        if (fea['Dist_N']==None):
          li.append("BLANK")
        else:
          li.append(fea['Dist_N'])

      li = sorted(set(li))
      self.dlg.comboBox_aoi_selectD.clear()
      self.dlg.comboBox_aoi_selectD.addItems(li)
      
    def get_blocks(self):
      print("called get Block")
      self.dist = self.dlg.comboBox_aoi_selectD.currentText()
      print("of district: ",self.dist)
      self.distFilter = "\"Dist_N\"='" + self.dist + "'"
      self.vlayerFilter = self.stateFilter + " and " + self.distFilter
      #print(self.vlayerFilter)
      expr = QgsExpression(self.vlayerFilter)
      distFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))

      li = []
      for fea in distFeas:
        if (fea['SubDist_N']==None):
          li.append("BLANK")
        else:
          li.append(fea['SubDist_N'])

      li = sorted(set(li))
      print("no of blocks:",len(li))

      self.dlg.comboBox_aoi_selectB.clear()
      self.dlg.comboBox_aoi_selectB.addItems(li)
      
    def get_villages(self):
      print("called get Villages")
      self.block = self.dlg.comboBox_aoi_selectB.currentText()
      self.blockFilter = "\"SubDist_N\"='" + self.block + "'"
      self.vlayerFilter = self.stateFilter + " and " + self.distFilter + " and " + self.blockFilter
      expr = QgsExpression(self.vlayerFilter)
      blockFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      
      li = []
      for fea in blockFeas:
        if (fea['VCT_N']==None):
            li.append("BLANK")
        else:
            li.append(str(fea['VCT_N']))
      
      li = sorted(set(li))      
      self.dlg.comboBox_aoi_selectV.clear()
      self.dlg.comboBox_aoi_selectV.addItems(li)

    def select_village(self):
      print("called select village")
      self.vlg = self.dlg.comboBox_aoi_selectV.currentText()
      self.vlgFilter = "\"VCT_N\"='"+self.vlg+"'"
      self.vlayerFilter = self.stateFilter + " and " + self.distFilter + " and " + self.blockFilter + " and " + self.vlgFilter
      self.vlayerFilter = self.vlayerFilter  # "\""+ self.vlayerFilter.replace("\"","\\\"") +"\""
      print(self.vlayerFilter)
      print(self.iface.activeLayer())
      # expr = QgsExpression(self.vlayerFilter)
      #print("is expression valid: ",checkExpression(expr))
      self.iface.activeLayer().selectByExpression(self.vlayerFilter)


    def zoom_village(self):
      print("called zoom to village")
      self.select_village()
      print(self.iface.setActiveLayer(self.vlayer))
      print(self.vlayer, self.iface.activeLayer())
      self.iface.actionZoomToSelected().trigger()
      print("zoom to Village triggered","\n")

      
    ##########################################################################
    ##                       Water Balance Layers                           ##
    ##########################################################################
    
    ####       POPULATE UI       ####

    def populate_lulc_choices(self):
      li = ["2000","2015","2016","2017","2018","2019"]
      self.dlg.comboBox_5.clear()
      self.dlg.comboBox_5.addItems(sorted(set(li)))
    
    def populate_layer_list(self,layer):
      if layer=='rain':
        start,end=(2000,2020)
      elif layer=='et':
        start,end=(2003,2020)
      elif layer=='sm':
        start,end=(2015,2020)
      elif layer=='groundwater':
        start,end=(1996,2016)
      elif layer=='surfacewater':
        start,end=(2000,2021)
      elif layer=='wbyear':
        start,end=(2000,2017)
      else:
        print("incorrect layer name provided to populate layer list")

      li = list(range(start,end))
      years = [str(yr) for yr in li]

      if layer=='rain':
        self.dlg.comboBox_9.clear()
        self.dlg.comboBox_9.addItems(sorted(years))
      elif layer=='et':
        self.dlg.comboBox_11.clear()
        self.dlg.comboBox_11.addItems(sorted(years))
      elif layer=='sm':
        self.dlg.comboBox_13.clear()
        self.dlg.comboBox_13.addItems(sorted(years))
      elif layer=='groundwater':
        self.dlg.comboBox_12.clear()
        self.dlg.comboBox_12.addItems(sorted(years))
      elif layer=='surfacewater':
        self.dlg.comboBox_10.clear()
        self.dlg.comboBox_10.addItems(sorted(years))
      elif layer=='wbyear':
        self.dlg.comboBox_6.clear()
        self.dlg.comboBox_6.addItems(sorted(years))
      else:
        print("incorrect layer name provided to populate layer list")

    ####      DEFINE LAYERS      ####

    def make_lulc_image(self):
      geeAssetString = 'users/cseicomms/lulc_13class/KA_' + str(int(self.lulc_yr)+1)
      print(geeAssetString)
      self.lulc = ee.Image(geeAssetString)
      print(type(self.lulc))

    def make_rain_image(self):
      rainColl = ee.ImageCollection("users/cseicomms/rainfall_imd")
      start = ee.Date.fromYMD(int(self.rain_year),6,1)
      end = ee.Date.fromYMD(int(self.rain_year)+1,5,31)
      self.rain = rainColl.filterDate(start,end).sum()
      print(type(self.rain))

    def make_et_image(self):
      geeAssetString = 'users/cseicomms/evapotranspiration_ssebop/wy' + self.et_year
      self.et = ee.Image(geeAssetString)
      print(type(self.et))

    def make_sw_image(self):
      print(type(self.sw_year),self.sw_year)
      y1str = 'users/cseicomms/surfacewater/preMonsoonVolume/' + self.sw_year
      y2str = 'users/cseicomms/surfacewater/preMonsoonVolume/' + str(int(self.sw_year) + 1)
      year1 = ee.Image(y1str)
      year2 = ee.Image(y2str)
      print(y1str,y2str)
      y1unmask = year1.subtract(year1)
      y2unmask = year2.subtract(year2)

      self.sw = year2.unmask(y1unmask).subtract(year1.unmask(y2unmask))
      print(type(self.sw))

    def make_gw_image(self):
      print(type(self.gw_year),self.gw_year)
      rcstr = 'users/cseicomms/groundwater/recharge/' + self.gw_year
      dcstr = 'users/cseicomms/groundwater/discharge/' + self.gw_year
      rc = ee.Image(rcstr)
      dc = ee.Image(dcstr)
      print(rcstr,dcstr)
      sy = 0.01
      self.gw = rc.subtract(dc).multiply(1000).multiply(sy)
      print(type(self.gw))

    def make_sm_image(self):
      smColl = ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture");
      print(type(self.sm_year),self.sm_year)

      year = int(self.sm_year)
      myFilter = ee.Filter.And(ee.Filter.calendarRange(year,year,'year'),ee.Filter.calendarRange(5,5,'month'))
      year1 = smColl.filter(myFilter).select('susm').median()

      year = int(self.sm_year) + 1
      myFilter = ee.Filter.And(ee.Filter.calendarRange(year,year,'year'),ee.Filter.calendarRange(5,5,'month'))
      year2 = smColl.filter(myFilter).select('susm').median()

      self.sm = year2.subtract(year1)
      print(type(self.sm))

    ####      ADD LAYERS TO MAP      ####

    def add_lulc_image(self):
      self.lulc_yr = self.dlg.comboBox_5.currentText()
      self.make_lulc_image()

      paletteLULC = ['02451E','06FC6D','FC0D06','28B505','750776','C713A9','C713A9',
                      'C713A9','E27FF9','E27FF9','E27FF9','765904','765904','765904',
                      'EAB828','EAB828','EAB828','092CEE','09EECB','Grey','Black']
      lulc_label = 'lulc_' + self.lulc_yr
      Map.addLayer(self.lulc, {'palette': paletteLULC, 'min': 0, 'max': 20}, lulc_label, True)
      Map.centerObject(self.lulc,10)

    def add_rain_image(self):
      self.rain_year = int(self.dlg.comboBox_9.currentText())
      self.make_rain_image()
      paletteRain = ['ff0','fff','00f']
      rainViz = {'min':400,'max':2000,'palette':paletteRain}
      rain_label = 'rain_' + str(self.rain_year)
      Map.addLayer(self.rain, rainViz, rain_label, True)
      self.rain = None
      self.rain_year = None
      self.project.setCrs(self.crs)
      print("crs set to 3857")

    def add_et_image(self):
      self.et_year = self.dlg.comboBox_11.currentText()
      self.make_et_image()
      et_label = 'et_' + self.et_year
      Map.addLayer(self.et,{'min':300,'max':1500},et_label,True)
      self.et = None
      self.et_year = None

    def add_sw_image(self):
      self.sw_year = self.dlg.comboBox_10.currentText()
      self.make_sw_image()
      paletteSW = ['#f00','#000','#00f']
      swViz = {'min':-80,'max':80,'palette':paletteSW}
      sw_label = 'sw_' + self.sw_year
      Map.addLayer(self.sw,swViz,sw_label,True)
      self.sw = None
      self.sw_year = None

    def add_gw_image(self):
      self.gw_year = self.dlg.comboBox_12.currentText()
      self.make_gw_image()
      paletteGW = ['#f00','#fff','#0f0']
      gwViz = {'min':-80,'max':80,'palette':paletteGW}
      gw_label = 'gw_' + self.gw_year
      Map.addLayer(self.gw,gwViz,gw_label,True)
      self.gw = None
      self.gw_year = None

    def add_sm_image(self):
      self.sm_year = self.dlg.comboBox_13.currentText()
      self.make_sm_image()
      paletteSM = ['#f00','#fff','#0f0']
      smViz = {'min':-80,'max':80,'palette':paletteSM}
      sm_label = 'sm_' + self.sm_year
      Map.addLayer(self.sm,smViz,sm_label,True)
      self.sm = None
      self.sm_year = None
    
    ####      CALC WATER BALANCE VALUES      ####
    def calc_rain_value(self):
      try:
        self.rain_value = str(round(self.rain.reduceRegion(ee.Reducer.median(),self.polygon,100).getInfo()['b1'])) + ' mm'
        print("rain value: ", self.rain_value)
      except:
        print(self.rain_year + " " + "rainfall image not found")
        self.rain_value = "NA"

    def calc_et_value(self):
      try:
        self.et_value = str(round(self.et.reduceRegion(ee.Reducer.median(),self.polygon,100).getInfo()['b1'])) + ' mm'
        print("et value: ", self.et_value)
      except:
        print(self.et_year + " " + "et image not found")
        self.et_value = "NA"

    def calc_sw_value(self):
      try:
        self.sw_value = str(round(self.sw.reduceRegion(ee.Reducer.sum(),self.polygon,100).getInfo()['Volume'])) + ' mm'
        print("sw value: ", self.sw_value)
      except:
        print(self.sw_year + " " + "surface water image not found")
        self.sw_value = "NA"

    def calc_gw_value(self):
      try:
        self.gw_value = str(round(self.gw.reduceRegion(ee.Reducer.median(),self.polygon,100).getInfo()['b1'])) + ' mm'
        print("gw value: ", self.gw_value)
      except:
        print(self.gw_year + " " + "groundwater image not found")
        self.gw_value = "NA"

    def calc_sm_value(self):
      try:
        self.sm_value = str(round(self.sm.reduceRegion(ee.Reducer.median(),self.polygon,100).getInfo()['susm'])) + ' mm'
        print("sm value: ", self.sm_value)
      except:
        print(self.sm_year + " " + "soil moisture image not found")
        self.sm_value = "NA"

    def calc_vill_area(self):
      self.select_village()
      vill = self.vlayer.getSelectedFeatures()

    def calc_water_balance(self):
      self.rain_year = self.et_year = self.gw_year = self.sw_year = self.sm_year = self.dlg.comboBox_6.currentText()
      self.make_rain_image()
      self.calc_rain_value()
      self.make_et_image()
      self.calc_et_value()
      self.make_sw_image()
      self.calc_sw_value()
      self.make_gw_image()
      self.calc_gw_value()
      self.make_sm_image()
      self.calc_sm_value()


    def print_water_balance(self):
      geometry = json.loads(self.iface.activeLayer().selectedFeatures()[0].geometry().coerceToType(QgsWkbTypes.MultiPolygon)[0].asJson())
      print(self.iface.activeLayer(),"\n")
      print(geometry['coordinates'])
      self.polygon = ee.Geometry.MultiPolygon(geometry['coordinates'])
      #print(self.polygon)

      self.calc_water_balance()

      project = QgsProject.instance()
      print("project title is: ",project.title())
      layout = QgsLayout(project)
      print("layout initialized")
      layout.initializeDefaults()

      template = os.path.join(cmd_folder,"resources","water_balance.qpt")
      print(type(template))

      with open(template) as f:
          template_content = f.read()
          print("got template_content")
      print(type(template_content))

      doc = QDomDocument()
      doc.setContent(template_content)
      print("initialized Q Dom Document")

      # adding to existing items
      items, ok = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)

      rain_label = layout.itemById('precipitation')
      print("got rainfall label")
      rain_label.setText(self.rain_value)

      et_label = layout.itemById('evapotranspiration')
      print("got evapotranspiration label")
      et_label.setText(self.et_value)

      sw_label = layout.itemById('surfacewater')
      print("got surfacewater label")
      sw_label.setText(self.sw_value)

      gw_label = layout.itemById('groundwater')
      print("got groundwater label")
      gw_label.setText(self.gw_value)

      sm_label = layout.itemById('soilmoisture')
      print("got soilmoisture label")
      sm_label.setText(self.sm_value)

      villname_label = layout.itemById('villname')
      print("got villname label")

      self.activelayername = self.iface.activeLayer().name()

      if ('Village' in self.activelayername):
        villname_label.setText(self.vlg)
      elif ('Watershed' in self.activelayername):
        villname_label.setText('Watershed')
      elif ('Custom' in self.activelayername):
        villname_label.setText('Custom')
      else:
        pass
      
      year_label = layout.itemById('year')
      print("got year label")
      year_label.setText(self.dlg.comboBox_6.currentText())

      exporter = QgsLayoutExporter(layout)
      output_image = os.path.join(home_dir, 'Desktop', '{}.png'.format("water_budget"))
      print(output_image)
      result = exporter.exportToImage(output_image, QgsLayoutExporter.ImageExportSettings())
      print(result)

    def crsChanged(self):
      print('CRS CHANGED')

    def run(self):
      self.crs = qgis.core.QgsCoordinateReferenceSystem(3857, qgis.core.QgsCoordinateReferenceSystem.EpsgCrsId)
      self.project = QgsProject.instance()
      self.project.setCrs(self.crs)
      print("crs set to 3857")

      self.dlg = RuralWaterDockWidget(
                  parent=self.iface.mainWindow(), iface=self.iface)
      logo_rect = QPixmap(os.path.join(cmd_folder,"resources","atree_logo_rect.png"))

      self.dlg.label_plugin_logo.setPixmap(logo_rect)

      self.dlg.show()
      
      self.dlg.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

      self.iface.addDockWidget(Qt.RightDockWidgetArea,self.dlg)
    
      self.populate_lulc_choices()
      self.populate_layer_list('rain')
      self.populate_layer_list('et')
      self.populate_layer_list('sm')
      self.populate_layer_list('groundwater')
      self.populate_layer_list('surfacewater')
      self.populate_layer_list('wbyear')
      
      #####     SIGNAL MAPPER for AOI SELECTION    #####
      self.signalmapperSOF = QSignalMapper()
      self.signalmapperSOF.mapped[int].connect(self.select_output_file)

      self.dlg.pushButton_aoi_selectVB.clicked.connect(self.signalmapperSOF.map)
      self.dlg.pushButton_aoi_selectWB.clicked.connect(self.signalmapperSOF.map)
      self.dlg.pushButton_aoi_selectCB.clicked.connect(self.signalmapperSOF.map)

      self.signalmapperSOF.setMapping(self.dlg.pushButton_aoi_selectVB, 0)
      self.signalmapperSOF.setMapping(self.dlg.pushButton_aoi_selectWB, 1)
      self.signalmapperSOF.setMapping(self.dlg.pushButton_aoi_selectCB, 2)

      #####     SIGNAL MAPPER for BOUNDARY ADDITION    #####
      self.signalmapperABL = QSignalMapper()
      self.signalmapperABL.mapped[int].connect(self.add_boundary_layer)

      self.dlg.lineEdit_aoi_selectVB.textChanged.connect(self.signalmapperABL.map)
      self.dlg.lineEdit_aoi_selectWB.textChanged.connect(self.signalmapperABL.map)
      self.dlg.lineEdit_aoi_selectCB.textChanged.connect(self.signalmapperABL.map)

      self.signalmapperABL.setMapping(self.dlg.lineEdit_aoi_selectVB, 0)
      self.signalmapperABL.setMapping(self.dlg.lineEdit_aoi_selectWB, 1)
      self.signalmapperABL.setMapping(self.dlg.lineEdit_aoi_selectCB, 2)

      #self.dlg.pushButton.clicked.connect(self.select_output_file)      # Select shape file 
      self.dlg.pushButton_2.clicked.connect(self.add_lulc_image)
      self.dlg.pushButton_3.clicked.connect(self.add_rain_image)
      self.dlg.pushButton_8.clicked.connect(self.add_et_image)
      self.dlg.pushButton_6.clicked.connect(self.add_sw_image)
      self.dlg.pushButton_7.clicked.connect(self.add_gw_image)
      self.dlg.pushButton_9.clicked.connect(self.add_sm_image)
      self.dlg.pushButton_10.clicked.connect(self.print_water_balance)
      self.dlg.comboBox_aoi_selectS.currentTextChanged.connect(self.get_districts)
      self.dlg.comboBox_aoi_selectD.currentTextChanged.connect(self.get_blocks)
      self.dlg.comboBox_aoi_selectB.currentTextChanged.connect(self.get_villages)
      self.dlg.comboBox_aoi_selectV.currentTextChanged.connect(self.zoom_village)
      self.project.crsChanged.connect(self.crsChanged)
      #self.dlg.comboBox_6.currentTextChanged.connect(self.show_rain_stats)
      #self.dlg.pushButton_3.clicked.connect(self.show_rain_stats)