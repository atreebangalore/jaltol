import os
import sys
sys.path.append(os.path.dirname(__file__))    # needed so resources.py can be found

from PyQt5 import uic
from PyQt5 import QtWidgets

WIDGET,BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'rw_dockwidget_base_trial_tabs.ui'), resource_suffix='')


class RuralWaterDockWidget(BASE, WIDGET):
    def __init__(self, parent=None, iface=None):
        super(RuralWaterDockWidget, self).__init__(parent)
        self.setupUi(self)