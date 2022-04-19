import os
import sys
sys.path.append(os.path.dirname(__file__))    # needed so resources.py can be found

from PyQt5 import uic
from PyQt5 import QtWidgets

WIDGET,BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui','jaltol_dockwidget.ui'), resource_suffix='')


class JaltolDockWidget(BASE, WIDGET):
    def __init__(self, parent=None, iface=None):
        super(JaltolDockWidget, self).__init__(parent)
        self.setupUi(self)