from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from Orange.base import Learner, Model, SklLearner, SklModel

__all__ = ["LearnerRegression", "ModelRegression",
           "SklModelRegression", "SklLearnerRegression"]


class LearnerRegression(Learner):

    def incompatibility_reason(self, domain):
        reason = None
        if len(domain.class_vars) > 1 and not self.supports_multiclass:
            reason = _tr.m[198, "Too many target variables."]
        elif not domain.has_continuous_class:
            reason = _tr.m[199, "Numeric target variable expected."]
        return reason


class ModelRegression(Model):
    pass


class SklModelRegression(SklModel, ModelRegression):
    pass


class SklLearnerRegression(SklLearner, LearnerRegression):
    __returns__ = SklModelRegression
