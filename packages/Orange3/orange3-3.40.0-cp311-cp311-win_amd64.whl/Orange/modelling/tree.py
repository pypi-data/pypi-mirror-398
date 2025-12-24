from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from Orange.classification import SklTreeLearner
from Orange.classification import TreeLearner as ClassificationTreeLearner
from Orange.modelling import Fitter, SklFitter
from Orange.regression import TreeLearner as RegressionTreeLearner
from Orange.regression.tree import SklTreeRegressionLearner
from Orange.tree import TreeModel

__all__ = ['SklTreeLearner', 'TreeLearner']


class SklTreeLearner(SklFitter):
    name = _tr.m[141, 'tree']

    __fits__ = {'classification': SklTreeLearner,
                'regression': SklTreeRegressionLearner}


class TreeLearner(Fitter):
    name = _tr.m[142, 'tree']

    __fits__ = {'classification': ClassificationTreeLearner,
                'regression': RegressionTreeLearner}

    __returns__ = TreeModel
