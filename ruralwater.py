import os
import ee
import sys
import inspect
from qgis.core import QgsProject,QgsVectorLayer,QgsProject,QgsFeature,QgsFeatureRequest,QgsExpression
from qgis.gui import *

from PyQt5.QtWidgets import QAction, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt     #contains Qt.BrushStyle

from datetime import datetime
from .ruralwater_dialog import RuralWaterDialog

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
      self.addLayer()
      
    def addLayer(self):
      print("called addLayer")
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
      
      self.getStates()
      
    def getStates(self):
      print("called get States")
      feas = self.vlayer.getFeatures()
      li = []
      for fea in feas:
        if (fea['stat_name']==None):
          li.append("BLANK")
        else:
          li.append(fea['stat_name'])
      self.dlg.comboBox.clear()
      self.dlg.comboBox.addItems(set(li))

    def getDistricts(self):
      print("called get Districts")
      feas = self.vlayer.getFeatures()
      li = []
      for fea in feas:
        if (fea['dist_name']==None):
          li.append("BLANK")
        else:
          li.append(fea['dist_name'])
      self.dlg.comboBox_2.clear()
      self.dlg.comboBox_2.addItems(set(li))

    def getBlocks(self):
      print("called get Block")
      dist = self.dlg.comboBox_2.currentText()
      print("chosen district:",dist)
      feas = self.vlayer.getFeatures()
      li = []
      for fea in feas:
        if (fea['dist_name']==dist):
            if (fea['sdst_name']==None):
                li.append("BLANK")
            else:
                li.append(fea['sdst_name'])
      self.dlg.comboBox_3.clear()
      self.dlg.comboBox_3.addItems(set(li))

    def getVillages(self):
      print("called get Villages")
      sdst = self.dlg.comboBox_3.currentText()
      print("chosen sub district:",sdst)
      feas = self.vlayer.getFeatures()
      li = []
      for fea in feas:
        if (fea['sdst_name']==sdst):
            if (fea['vlgcd2011']==None):
                li.append("BLANK")
            else:
                li.append(fea['vlgcd2011'])
      self.dlg.comboBox_4.clear()
      self.dlg.comboBox_4.addItems(set(li))
    
    def zoomVillage(self):
      print("called zoom to village")
      vlg = self.dlg.comboBox_4.currentText()
      print("chosen village:",vlg)
      vlgstring = "\"vlgcd2011\"='"+vlg+"'"
      print("Expression text: ",vlgstring)
      expr = QgsExpression(vlgstring)
      
      vlgFea = self.vlayer.getFeatures(QgsFeatureRequest(expr))
      self.vlayer.selectByExpression(vlgstring)
      self.iface.actionZoomToSelected().trigger()
      
    def show_time(self):
      now = datetime.now()
      current_time = now.strftime("%H:%M:%S")
      self.iface.messageBar().pushMessage('Time is {}'.format(current_time))
        
    def run(self):
      self.dlg = RuralWaterDialog()
      self.dlg.show()
      
      self.dlg.pushButton.clicked.connect(self.select_output_file)      # Select shape file 
      self.dlg.comboBox.currentTextChanged.connect(self.getDistricts)
      self.dlg.comboBox_2.currentTextChanged.connect(self.getBlocks)
      self.dlg.comboBox_3.currentTextChanged.connect(self.getVillages)
      self.dlg.comboBox_4.currentTextChanged.connect(self.zoomVillage)