
from PyQt5.QtWidgets import QFileDialog

def select_output_file(self):
    print("called select_output_file")
    filename, _filter = QFileDialog.getOpenFileName(                  # use file dialog to get filename 
    self.dlg, "Select shape file ","", '*.shp')
    self.dlg.lineEdit.setText(filename)
    self.addLayer()