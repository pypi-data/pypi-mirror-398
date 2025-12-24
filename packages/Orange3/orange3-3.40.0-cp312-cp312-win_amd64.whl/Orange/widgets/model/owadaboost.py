from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QFormLayout, QLabel

from Orange.base import Learner
from Orange.data import Table
from Orange.modelling import SklAdaBoostLearner, SklTreeLearner
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.utils.owlearnerwidget import OWBaseLearner
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Msg, Input


class OWAdaBoost(OWBaseLearner):
    name = "AdaBoost"
    description = (_tr.m[2164, "An ensemble meta-algorithm that combines weak learners "] + _tr.m[2165, "and adapts to the 'hardness' of each training sample. "])
    icon = "icons/AdaBoost.svg"
    replaces = [
        "Orange.widgets.classify.owadaboost.OWAdaBoostClassification",
        "Orange.widgets.regression.owadaboostregression.OWAdaBoostRegression",
    ]
    priority = 80
    keywords = _tr.m[2166, "adaboost, boost"]

    LEARNER = SklAdaBoostLearner

    class Inputs(OWBaseLearner.Inputs):
        learner = Input(_tr.m[2167, "Learner"], Learner)

    #: Losses for regression problems
    losses = [_tr.m[2168, "Linear"], _tr.m[2169, "Square"], _tr.m[2170, "Exponential"]]

    n_estimators = Setting(50)
    learning_rate = Setting(1.)
    loss_index = Setting(0)
    use_random_seed = Setting(False)
    random_seed = Setting(0)

    DEFAULT_BASE_ESTIMATOR = SklTreeLearner()

    class Error(OWBaseLearner.Error):
        no_weight_support = Msg(_tr.m[2171, 'The base learner does not support weights.'])

    def add_main_layout(self):
        # this is part of init, pylint: disable=attribute-defined-outside-init
        grid = QFormLayout()
        gui.widgetBox(self.controlArea, box=True, orientation=grid)
        self.base_estimator = self.DEFAULT_BASE_ESTIMATOR
        self.base_label = QLabel(self.base_estimator.name.title())
        grid.addRow(_tr.m[2172, "Base estimator:"], self.base_label)

        self.n_estimators_spin = gui.spin(
            None, self, "n_estimators", 1, 10000,
            controlWidth=80, alignment=Qt.AlignRight,
            callback=self.settings_changed)
        grid.addRow(_tr.m[2173, "Number of estimators:"], self.n_estimators_spin)

        self.learning_rate_spin = gui.doubleSpin(
            None, self, "learning_rate", 1e-5, 1.0, 1e-5, decimals=5,
            alignment=Qt.AlignRight,
            callback=self.settings_changed)
        grid.addRow(_tr.m[2174, "Learning rate:"], self.learning_rate_spin)

        self.reg_algorithm_combo = gui.comboBox(
            None, self, "loss_index", items=self.losses,
            callback=self.settings_changed)
        grid.addRow(_tr.m[2175, "Loss (regression):"], self.reg_algorithm_combo)

        box = gui.widgetBox(self.controlArea, box=_tr.m[2176, "Reproducibility"])
        self.random_seed_spin = gui.spin(
            box, self, "random_seed", 0, 2 ** 31 - 1, controlWidth=80,
            label=_tr.m[2177, "Fixed seed for random generator:"], alignment=Qt.AlignRight,
            callback=self.settings_changed, checked="use_random_seed",
            checkCallback=self.settings_changed)

    def create_learner(self):
        if self.base_estimator is None:
            return None
        return self.LEARNER(
            estimator=self.base_estimator,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            random_state=self.random_seed,
            preprocessors=self.preprocessors,
            loss=self.losses[self.loss_index].lower())

    @Inputs.learner
    def set_base_learner(self, learner):
        # base_estimator is defined in add_main_layout
        # pylint: disable=attribute-defined-outside-init
        self.Error.no_weight_support.clear()
        if learner and not learner.supports_weights:
            # Clear the error and reset to default base learner
            self.Error.no_weight_support()
            self.base_estimator = None
            self.base_label.setText(_tr.m[2178, "INVALID"])
        else:
            self.base_estimator = learner or self.DEFAULT_BASE_ESTIMATOR
            self.base_label.setText(self.base_estimator.name.title())
        self.learner = self.model = None

    def get_learner_parameters(self):
        return ((_tr.m[2179, "Base estimator"], self.base_estimator),
                (_tr.m[2180, "Number of estimators"], self.n_estimators),
                (_tr.m[2181, "Loss (regression)"], self.losses[
                    self.loss_index].capitalize()))


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWAdaBoost).run(Table("iris"))
