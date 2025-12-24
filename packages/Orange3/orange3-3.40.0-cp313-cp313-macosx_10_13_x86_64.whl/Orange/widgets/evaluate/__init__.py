"""
========
Evaluate
========

Evaluating models.

"""
from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator

NAME = _tr.m[1789, "Evaluate"]

ID = "orange.widgets.evaluate"

DESCRIPTION = _tr.m[1790, "Evaluate model performance"]

BACKGROUND = "#C3F3F3"

ICON = "icons/Category-Evaluate.svg"

PRIORITY = 5
