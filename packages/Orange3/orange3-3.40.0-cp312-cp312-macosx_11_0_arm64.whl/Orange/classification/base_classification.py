from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from Orange.base import Learner, Model, SklLearner, SklModel

__all__ = ["LearnerClassification", "ModelClassification",
           "SklModelClassification", "SklLearnerClassification"]


class LearnerClassification(Learner):

    def incompatibility_reason(self, domain):
        reason = None
        if len(domain.class_vars) > 1 and not self.supports_multiclass:
            reason = _tr.m[40, "Too many target variables."]
        elif not domain.has_discrete_class:
            reason = _tr.m[41, "Categorical class variable expected."]
        return reason


class ModelClassification(Model):
    def predict_proba(self, data):
        return self(data, ret=Model.Probs)


class SklModelClassification(SklModel, ModelClassification):
    pass


class SklLearnerClassification(SklLearner, LearnerClassification):
    __returns__ = SklModelClassification
