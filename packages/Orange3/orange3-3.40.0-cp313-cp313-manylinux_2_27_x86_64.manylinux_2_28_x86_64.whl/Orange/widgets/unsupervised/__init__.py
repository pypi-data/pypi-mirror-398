"""
============
Unsupervised
============

Unsupervised learning.

"""
from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator

NAME = _tr.m[2635, "Unsupervised"]

ID = "orange.widgets.unsupervised"

DESCRIPTION = _tr.m[2636, "Unsupervised learning."]

BACKGROUND = "#CAE1EF"

ICON = "icons/Category-Unsupervised.svg"

PRIORITY = 6
