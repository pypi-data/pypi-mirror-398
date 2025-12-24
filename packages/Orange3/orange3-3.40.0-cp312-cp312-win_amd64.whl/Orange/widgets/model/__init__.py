"""
======
Models
======

Classifiers and regressors.

"""
from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator

NAME = "Model"

ID = "orange.widgets.model"

DESCRIPTION = _tr.m[2163, "Prediction"]

BACKGROUND = "#FAC1D9"

ICON = "icons/Category-Model.svg"

PRIORITY = 4
