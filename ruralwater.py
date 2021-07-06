import os
import ee
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#from matplotlib.figure import Figure
#from matplotbib import axes
  
import sys
import json
import inspect
import qgis.core
from qgis.core import QgsProject,QgsLayout,QgsLayoutExporter,QgsReadWriteContext,QgsVectorLayer,QgsFeature,QgsFeatureRequest,QgsExpression
from qgis.gui import *

from PyQt5.QtWidgets import QAction, QFileDialog, QDockWidget
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5.QtCore import Qt     #contains Qt.BrushStyle
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
      self.action = QAction(QIcon(icon), 'Rural Water', self.iface.mainWindow())    # create QAction
      self.action.triggered.connect(self.run)                           # if QAction triggered, run
      self.iface.addPluginToMenu('&Rural Water>', self.action)       # add action to menu
      self.iface.addToolBarIcon(self.action)                            # add action to tool bar 
      self.first_start = True

    def unload(self):
      self.iface.removeToolBarIcon(self.action)                         # remove action from tool bar
      self.iface.removePluginMenu('&Rural Water', self.action)      # remove action from plugin menu
      del self.action

    def select_output_file(self):
      print("called select_output_file")
      filename, _filter = QFileDialog.getOpenFileName(                  # use file dialog to get filename 
        self.dlg, "Select shape file ","", '*.shp')
      self.dlg.lineEdit.setText(filename)
      self.add_boundary_layer()
      
    def add_boundary_layer(self):
      print("called add_boundary_layer")
      self.filename = self.dlg.lineEdit.text()
      print(self.filename)
      self.layername = os.path.basename(self.filename).split(".")[0]
      print(self.layername)
      self.vlayer = QgsVectorLayer(self.filename, self.layername, "ogr")
      QgsProject.instance().addMapLayer(self.vlayer)
      
      alayer = self.iface.activeLayer()
      single_symbol_renderer = alayer.renderer()
      symbol = single_symbol_renderer.symbol()
      symbol.symbolLayer(0).setBrushStyle(Qt.BrushStyle(Qt.NoBrush))
      
      self.get_states()
      
    def get_states(self):
      print("called get States")
      li = self.vlayer.uniqueValues(1)
      if qgis.core.NULL in li:
          li.remove(qgis.core.NULL)
      self.dlg.comboBox.clear()
      self.dlg.comboBox.addItems(li)

    def get_districts(self):
      print("called get Districts")
      self.state = self.dlg.comboBox.currentText()
      stateFilter = "\"State_N\"='" + self.state + "'"
      expr = QgsExpression(stateFilter)
      stateFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      print(stateFeas)

      li = []
      for fea in stateFeas:
        if (fea['Dist_N']==None):
          li.append("BLANK")
        else:
          li.append(fea['Dist_N'])

      self.dlg.comboBox_2.clear()
      self.dlg.comboBox_2.addItems(set(li))
      
    def get_blocks(self):
      print("called get Block")
      self.dist = self.dlg.comboBox_2.currentText()
      distFilter = "\"Dist_N\"='" + self.dist + "'"
      expr = QgsExpression(distFilter)
      distFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      
      li = []
      for fea in distFeas:
        if (fea['SubDist_N']==None):
          li.append("BLANK")
        else:
          li.append(fea['SubDist_N'])

      self.dlg.comboBox_3.clear()
      self.dlg.comboBox_3.addItems(set(li))
      
    def get_villages(self):
      print("called get Villages")
      self.block = self.dlg.comboBox_3.currentText()
      blockFilter = "\"SubDist_N\"='" + self.block + "'"
      expr = QgsExpression(blockFilter)
      blockFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      
      li = []
      for fea in blockFeas:
        if (fea['VCT_Cd']==None):
            li.append("BLANK")
        else:
            li.append(str(fea['VCT_Cd']))
            
      self.dlg.comboBox_4.clear()
      self.dlg.comboBox_4.addItems(set(li))
    
    def zoom_village(self):
      print("called zoom to village")
      vlg = self.dlg.comboBox_4.currentText()
      vlgstring = "\"VCT_Cd\"='"+vlg+"'"
      expr = QgsExpression(vlgstring)
      vlgFea = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      self.vlayer.selectByExpression(vlgstring)
      self.iface.actionZoomToSelected().trigger()
      
    
    def show_rain_stats(self):
      figNos = plt.get_fignums()
      if len(figNos)>0:
          print("figure already exists")
          for no in figNos:
              plt.close(no)
      print("get Rain Stats called")
      self.rainDist = self.dlg.lineEdit_2.text()
      self.rainYear = self.dlg.comboBox_6.currentText()
      distRain = self.df.loc[(self.df.District==self.rainDist) & (self.df.Year==int(self.rainYear)),"January":"December"]
      
      fig,ax = plt.subplots()
      ax.bar(distRain.columns,distRain.iloc[0])
      plt.show()
    
    def populate_lulc_choices(self):
      li = ["2001","2009","2016","2017","2018","2019","2020"]
      self.dlg.comboBox_5.clear()
      self.dlg.comboBox_5.addItems(sorted(set(li)))
    
    def populate_rain_year_choices(self):
      li = list(range(2000,2021))
      years = [str(yr) for yr in li]
      self.dlg.comboBox_9.clear()
      self.dlg.comboBox_9.addItems(sorted(years))
      
    def populate_et_year_choices(self):
      li = list(range(2003,2021))
      years = [str(yr) for yr in li]
      self.dlg.comboBox_11.clear()
      self.dlg.comboBox_11.addItems(sorted(years))
    
    def add_lulc_image(self):
      chosenLULCYr = self.dlg.comboBox_5.currentText()
      geeAssetString = 'users/cseicomms/lulc_13class/KA_' + chosenLULCYr
      print(geeAssetString)
      image = ee.Image(geeAssetString)
      print(image)
      paletteLULC = ['02451E','06FC6D','FC0D06','28B505','750776','C713A9','C713A9','C713A9','E27FF9','E27FF9','E27FF9','765904','765904','765904','EAB828','EAB828','EAB828','092CEE','09EECB','Grey','Black']
      lulc_label = 'lulc_' + chosenLULCYr
      Map.addLayer(image, {'palette': paletteLULC, 'min': 0, 'max': 20}, lulc_label, True)
      Map.centerObject(image,10)
    
    def add_rain_image(self):
      rainColl = ee.ImageCollection("users/cseicomms/rainfall_imd")
      chosenRainYr = int(self.dlg.comboBox_9.currentText())
      start = ee.Date.fromYMD(chosenRainYr,6,1)
      end = ee.Date.fromYMD(chosenRainYr+1,5,31)
      rain = rainColl.filterDate(start,end).sum()
      print(rain)
      paletteRain = ['ff0','fff','00f']
      rainViz = {'min':400,'max':2000,'palette':paletteRain}
      rain_label = 'rain_' + str(chosenRainYr)
      Map.addLayer(rain, rainViz, rain_label, True)

    def add_et_image(self):
      chosenETYr = self.dlg.comboBox_11.currentText()
      geeAssetString = 'users/cseicomms/evapotranspiration_ssebop/wy' + chosenETYr
      image = ee.Image(geeAssetString)
      et_label = 'et_' + chosenETYr
      Map.addLayer(image,{'min':300,'max':1500},et_label,True)

    def query_et_image(self):
      # geometry = json.loads(self.vlayer.selectedFeatures()[0].geometry().asJson())
      # print(geometry)
      # polygon = ee.Geometry.MultiPolygon(geometry['coordinates'])
      # print(polygon)
      project = QgsProject.instance()
      print("project title is: ",project.title())
      layout = QgsLayout(project)
      print("layout initialized")
      layout.initializeDefaults()

      print("query et image called")
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
      prec_label = layout.itemById('precipitation')
      print("got precipitation label")
      prec_label.setText('1000')

      exporter = QgsLayoutExporter(layout)
      # output_image = os.path.join(home_dir, 'Desktop', '{}.png'.format("sample"))
      output_image = os.path.join(cmd_folder,"resources",'{}.png'.format("sample"))
      print(output_image)
      result = exporter.exportToImage(output_image, QgsLayoutExporter.ImageExportSettings())
      print(result)

    def run(self):
      #imd_path = "https://storage.googleapis.com/imd-precipitation-historical-districts/IMD_Precipitation_TN_2004_2011.csv"

      self.dlg = RuralWaterDockWidget(
                  parent=self.iface.mainWindow(), iface=self.iface)
      logo_rect = QPixmap(os.path.join(cmd_folder,"resources","atree_logo_rect.png"))

      self.dlg.label_7.setPixmap(logo_rect)

      self.dlg.show()
      
      self.dlg.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

      self.iface.addDockWidget(Qt.RightDockWidgetArea,self.dlg)
    
      self.populate_lulc_choices()
      self.populate_rain_year_choices()
      self.populate_et_year_choices()
      
      self.dlg.pushButton.clicked.connect(self.select_output_file)      # Select shape file 
      self.dlg.pushButton_2.clicked.connect(self.add_lulc_image)
      self.dlg.pushButton_8.clicked.connect(self.add_et_image)
      self.dlg.pushButton_3.clicked.connect(self.add_rain_image)
      self.dlg.pushButton_10.clicked.connect(self.query_et_image)
      self.dlg.comboBox.currentTextChanged.connect(self.get_districts)
      self.dlg.comboBox_2.currentTextChanged.connect(self.get_blocks)
      self.dlg.comboBox_3.currentTextChanged.connect(self.get_villages)
      self.dlg.comboBox_4.currentTextChanged.connect(self.zoom_village)
      #self.dlg.comboBox_6.currentTextChanged.connect(self.show_rain_stats)
      #self.dlg.pushButton_3.clicked.connect(self.show_rain_stats)