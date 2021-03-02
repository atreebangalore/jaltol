import os
import ee
import pandas as pd
import sys
import inspect
import qgis.core
from qgis.core import QgsProject,QgsVectorLayer,QgsProject,QgsFeature,QgsFeatureRequest,QgsExpression
from qgis.gui import *

from PyQt5.QtWidgets import QAction, QFileDialog, QDockWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt     #contains Qt.BrushStyle

from datetime import datetime
from .ruralwater_dialog import RuralWaterDialog
from gee import Map
from vectors import getLocalBoundaries

print(dir(getLocalBoundaries))   # functions within module aren't registering.. dunno why

print(ee.String('Hello World from EE!').getInfo())
inspect_getfile = inspect.getfile(inspect.currentframe())
cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

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
      stateFilter = "\"stat_name\"='" + self.state + "'"
      expr = QgsExpression(stateFilter)
      stateFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      
      li = []
      for fea in stateFeas:
        if (fea['dist_name']==None):
          li.append("BLANK")
        else:
          li.append(fea['dist_name'])

      self.dlg.comboBox_2.clear()
      self.dlg.comboBox_2.addItems(set(li))
      
      
    def get_blocks(self):
      print("called get Block")
      self.dist = self.dlg.comboBox_2.currentText()
      distFilter = "\"dist_name\"='" + self.dist + "'"
      expr = QgsExpression(distFilter)
      distFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      
      li = []
      for fea in distFeas:
        if (fea['sdst_name']==None):
          li.append("BLANK")
        else:
          li.append(fea['sdst_name'])

      self.dlg.comboBox_3.clear()
      self.dlg.comboBox_3.addItems(set(li))
      
#      distRain = self.df.loc[self.df.District=="Thanjavur"]
#      rainStats = distRain.January.mean()
#      self.dlg.lineEdit_3.setText("Mean January rainfall 2004-2011 in {dist} is:".format(dist="Thanjavur") + str(rainStats))
      
    def get_villages(self):
      print("called get Villages")
      self.block = self.dlg.comboBox_3.currentText()
      blockFilter = "\"sdst_name\"='" + self.block + "'"
      expr = QgsExpression(blockFilter)
      blockFeas = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      
      li = []
      for fea in blockFeas:
        if (fea['vlgcd2011']==None):
            li.append("BLANK")
        else:
            li.append(fea['vlgcd2011'])
            
      self.dlg.comboBox_4.clear()
      self.dlg.comboBox_4.addItems(set(li))
    
    def zoom_village(self):
      print("called zoom to village")
      vlg = self.dlg.comboBox_4.currentText()
      vlgstring = "\"vlgcd2011\"='"+vlg+"'"
      expr = QgsExpression(vlgstring)
      vlgFea = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      self.vlayer.selectByExpression(vlgstring)
      self.iface.actionZoomToSelected().trigger()
      
    def show_time(self):
      now = datetime.now()
      current_time = now.strftime("%H:%M:%S")
      self.iface.messageBar().pushMessage('Time is {}'.format(current_time))
    
    def getRainStats(self):
      distRain = self.df.loc[self.df.District==self.dist]
      rainStats = distRain.January.mean()
      self.dlg.lineEdit_3.clear()
      self.dlg.lineEdit_3.setText("Mean January rainfall 2004-2011 in {dist} is:".format(dist=self.dist) + str(rainStats))
    
    def populate_lulc_choices(self):
      li = ["2010_11","2011_12","2012_13","2013_14","2014_15","2015_16","2016_17","2017_18","2018_19","2019_20","2020_21"]
      self.dlg.comboBox_5.clear()
      self.dlg.comboBox_5.addItems(set(li))
        
    def add_lulc_image(self):
      chosenLULCYr = self.dlg.comboBox_5.currentText()
      geeAssetString = 'users/gsnshinde/UPSCAPE_LULCFInal/LULC_' + chosenLULCYr + 'Class'
      image = ee.Image(geeAssetString)
      paletteLULC = ['02451E','06FC6D','FC0D06','28B505','750776','C713A9','C713A9','C713A9','E27FF9','E27FF9','E27FF9','765904','765904','765904','EAB828','EAB828','EAB828','092CEE','09EECB','Grey','Black']
      Map.addLayer(image, {'palette': paletteLULC, 'min': 0, 'max': 20}, 'lulc 2020_21', True)
        
    def run(self):
      imd_path = "https://storage.googleapis.com/imd-precipitation-historical-districts/IMD_Precipitation_TN_2004_2011.csv"
      self.df = pd.read_csv(imd_path)
      print(type(self.df))  
      self.dlg = RuralWaterDialog()
      self.dlg.show()
      
      self.populate_lulc_choices()
      self.dlg.pushButton.clicked.connect(self.select_output_file)      # Select shape file 
      self.dlg.pushButton_2.clicked.connect(self.add_lulc_image)
      self.dlg.comboBox.currentTextChanged.connect(self.get_districts)
      self.dlg.comboBox_2.currentTextChanged.connect(self.get_blocks)
      self.dlg.comboBox_3.currentTextChanged.connect(self.get_villages)
      self.dlg.comboBox_4.currentTextChanged.connect(self.zoom_village)
#      self.dlg.lineEdit_3.textChanged.connect(self.getRainStats)