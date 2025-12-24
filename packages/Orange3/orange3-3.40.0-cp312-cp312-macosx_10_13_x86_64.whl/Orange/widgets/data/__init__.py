"""
====
Data
====

Data manipulation.

"""
from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator

NAME = _tr.m[217, "Data"]

ID = "orange.widgets.data"

DESCRIPTION = _tr.m[218, """Data manipulation"""]

ICON = "icons/Category-Data.svg"

BACKGROUND = "#FFD39F"

PRIORITY = 1
