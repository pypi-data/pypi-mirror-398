from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
import copy

from Orange.classification import CalibratedLearner, ThresholdLearner, \
    NaiveBayesLearner
from Orange.data import Table
from Orange.modelling import Learner
from Orange.widgets import gui
from Orange.widgets.widget import Input
from Orange.widgets.settings import Setting
from Orange.widgets.utils.owlearnerwidget import OWBaseLearner
from Orange.widgets.utils.widgetpreview import WidgetPreview


class OWCalibratedLearner(OWBaseLearner):
    name = _tr.m[2182, "Calibrated Learner"]
    description = (_tr.m[2183, "Wraps another learner with probability calibration and "] + _tr.m[2184, "decision threshold optimization"])
    icon = "icons/CalibratedLearner.svg"
    priority = 20
    keywords = _tr.m[2185, "calibrated learner, calibration, threshold"]

    LEARNER = CalibratedLearner

    SigmoidCalibration, IsotonicCalibration, NoCalibration = range(3)
    CalibrationOptions = (_tr.m[2186, "Sigmoid calibration"],
                          _tr.m[2187, "Isotonic calibration"],
                          _tr.m[2188, "No calibration"])
    CalibrationShort = (_tr.m[2189, "Sigmoid"], _tr.m[2190, "Isotonic"], "")
    CalibrationMap = {
        SigmoidCalibration: CalibratedLearner.Sigmoid,
        IsotonicCalibration: CalibratedLearner.Isotonic}

    OptimizeCA, OptimizeF1, NoThresholdOptimization = range(3)
    ThresholdOptions = (_tr.m[2191, "Optimize classification accuracy"],
                        _tr.m[2192, "Optimize F1 score"],
                        _tr.m[2193, "No threshold optimization"])
    ThresholdShort = (_tr.m[2194, "CA"], _tr.m[2195, "F1"], "")
    ThresholdMap = {
        OptimizeCA: ThresholdLearner.OptimizeCA,
        OptimizeF1: ThresholdLearner.OptimizeF1}

    learner_name = Setting("", schema_only=True)
    calibration = Setting(SigmoidCalibration)
    threshold = Setting(OptimizeCA)

    class Inputs(OWBaseLearner.Inputs):
        base_learner = Input(_tr.m[2196, "Base Learner"], Learner)

    def __init__(self):
        super().__init__()
        self.base_learner = None

    def add_main_layout(self):
        gui.radioButtons(
            self.controlArea, self, "calibration", self.CalibrationOptions,
            box=_tr.m[2197, "Probability calibration"],
            callback=self.calibration_options_changed)
        gui.radioButtons(
            self.controlArea, self, "threshold", self.ThresholdOptions,
            box=_tr.m[2198, "Decision threshold optimization"],
            callback=self.calibration_options_changed)

    @Inputs.base_learner
    def set_learner(self, learner):
        self.base_learner = learner
        self._set_default_name()
        self.learner = self.model = None

    def _set_default_name(self):
        if self.base_learner is None:
            self.set_default_learner_name("")
        else:
            name = " + ".join(part for part in (
                self.base_learner.name.title(),
                self.CalibrationShort[self.calibration],
                self.ThresholdShort[self.threshold]) if part)
            self.set_default_learner_name(name)

    def calibration_options_changed(self):
        self._set_default_name()
        self.apply()

    def create_learner(self):
        if self.base_learner is None:
            return None
        learner = self.base_learner
        if self.calibration != self.NoCalibration:
            learner = CalibratedLearner(learner,
                                        self.CalibrationMap[self.calibration])
        if self.threshold != self.NoThresholdOptimization:
            learner = ThresholdLearner(learner,
                                       self.ThresholdMap[self.threshold])
        if learner is self.base_learner:
            learner = copy.deepcopy(learner)
        if self.preprocessors:
            learner.preprocessors = (self.preprocessors, )
        assert learner is not self.base_learner
        return learner

    def get_learner_parameters(self):
        return ((_tr.m[2199, "Calibrate probabilities"],
                 self.CalibrationOptions[self.calibration]),
                (_tr.m[2200, "Threshold optimization"],
                 self.ThresholdOptions[self.threshold]))


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWCalibratedLearner).run(
        Table("heart_disease"),
        set_learner=NaiveBayesLearner())
