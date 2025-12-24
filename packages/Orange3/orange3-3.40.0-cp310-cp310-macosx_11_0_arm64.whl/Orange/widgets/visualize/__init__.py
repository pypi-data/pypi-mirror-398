"""
=========
Visualize
=========

Widgets for data visualization.

"""
from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator

NAME = _tr.m[3440, "Visualize"]

ID = "orange.widgets.visualize"

DESCRIPTION = _tr.m[3441, "Data visualization"]

BACKGROUND = "#FFB7B1"

ICON = "icons/Category-Visualize.svg"

PRIORITY = 2
