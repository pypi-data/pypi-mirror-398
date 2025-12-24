from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from itertools import chain

from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QLayout, QSizePolicy

from Orange.data import Table, Domain, ContinuousVariable, StringVariable
from Orange.regression.linear import (
    LassoRegressionLearner, LinearRegressionLearner,
    RidgeRegressionLearner, ElasticNetLearner
)
from Orange.widgets import settings, gui
from Orange.widgets.utils.owlearnerwidget import OWBaseLearner
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Output


class OWLinearRegression(OWBaseLearner):
    name = _tr.m[2282, "Linear Regression"]
    description = (_tr.m[2283, "A linear regression algorithm with optional L1 (LASSO), "] + _tr.m[2284, "L2 (ridge) or L1L2 (elastic net) regularization."])
    icon = "icons/LinearRegression.svg"
    replaces = [
        "Orange.widgets.regression.owlinearregression.OWLinearRegression",
    ]
    priority = 60
    keywords = _tr.m[2285, "linear regression, ridge, lasso, elastic net"]

    LEARNER = LinearRegressionLearner

    class Outputs(OWBaseLearner.Outputs):
        coefficients = Output(_tr.m[2286, "Coefficients"], Table, explicit=True)

    #: Types
    REGULARIZATION_TYPES = [_tr.m[2287, "No regularization"], _tr.m[2288, "Ridge regression (L2)"],
                            _tr.m[2289, "Lasso regression (L1)"], _tr.m[2290, "Elastic net regression"]]
    OLS, Ridge, Lasso, Elastic = 0, 1, 2, 3

    ridge = settings.Setting(False)
    reg_type = settings.Setting(OLS)
    alpha_index = settings.Setting(0)
    l2_ratio = settings.Setting(0.5)
    fit_intercept = settings.Setting(True)
    autosend = settings.Setting(True)

    alphas = list(chain([x / 10000 for x in range(1, 10)],
                        [x / 1000 for x in range(1, 20)],
                        [x / 100 for x in range(2, 20)],
                        [x / 10 for x in range(2, 9)],
                        range(1, 20),
                        range(20, 100, 5),
                        range(100, 1001, 100)))

    def add_main_layout(self):
        # this is part of init, pylint: disable=attribute-defined-outside-init
        box = gui.hBox(self.controlArea, _tr.m[2291, "Parameters"])
        gui.checkBox(box, self, "fit_intercept",
                     _tr.m[2292, "Fit intercept (unchecking it fixes it to zero)"],
                     callback=self._intercept_changed)

        box = gui.hBox(self.controlArea, _tr.m[2293, "Regularization"])
        gui.radioButtons(box, self, "reg_type",
                         btnLabels=self.REGULARIZATION_TYPES,
                         callback=self._reg_type_changed)

        self.alpha_box = box2 = gui.vBox(box, margin=10)
        gui.widgetLabel(box2, _tr.m[2294, "Regularization strength:"])
        gui.hSlider(
            box2, self, "alpha_index",
            minValue=0, maxValue=len(self.alphas) - 1,
            callback=self._alpha_changed, createLabel=False)
        box3 = gui.hBox(box2)
        box3.layout().setAlignment(Qt.AlignCenter)
        self.alpha_label = gui.widgetLabel(box3, "")
        self._set_alpha_label()

        box4 = gui.vBox(box2, margin=0)
        gui.widgetLabel(box4, _tr.m[2295, "Elastic net mixing:"])
        box5 = gui.hBox(box4)
        gui.widgetLabel(box5, "L1")
        self.l2_ratio_slider = gui.hSlider(
            box5, self, "l2_ratio", minValue=0.01, maxValue=0.99,
            intOnly=False, createLabel=False, width=120,
            step=0.01, callback=self._l2_ratio_changed)
        gui.widgetLabel(box5, "L2")
        self.l2_ratio_label = gui.widgetLabel(
            box4, "",
            sizePolicy=(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self.l2_ratio_label.setAlignment(Qt.AlignCenter)

        box5 = gui.hBox(self.controlArea)
        box5.layout().setAlignment(Qt.AlignCenter)
        self._set_l2_ratio_label()
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.controls.alpha_index.setEnabled(self.reg_type != self.OLS)
        self.l2_ratio_slider.setEnabled(self.reg_type == self.Elastic)

    def _intercept_changed(self):
        self.apply()

    def _reg_type_changed(self):
        self.controls.alpha_index.setEnabled(self.reg_type != self.OLS)
        self.l2_ratio_slider.setEnabled(self.reg_type == self.Elastic)
        self.apply()

    def _set_alpha_label(self):
        self.alpha_label.setText(_tr.m[2296, "Alpha: {}"].format(self.alphas[self.alpha_index]))

    def _alpha_changed(self):
        self._set_alpha_label()
        self.apply()

    def _set_l2_ratio_label(self):
        self.l2_ratio_label.setText(
            "{:.{}f} : {:.{}f}".format(1 - self.l2_ratio, 2, self.l2_ratio, 2))

    def _l2_ratio_changed(self):
        self._set_l2_ratio_label()
        self.apply()

    def create_learner(self):
        alpha = self.alphas[self.alpha_index]
        preprocessors = self.preprocessors
        args = dict(preprocessors=preprocessors,
                    fit_intercept=self.fit_intercept)
        if self.reg_type == OWLinearRegression.OLS:
            learner = LinearRegressionLearner(**args)
        elif self.reg_type == OWLinearRegression.Ridge:
            learner = RidgeRegressionLearner(alpha=alpha, **args)
        elif self.reg_type == OWLinearRegression.Lasso:
            learner = LassoRegressionLearner(alpha=alpha, **args)
        elif self.reg_type == OWLinearRegression.Elastic:
            learner = ElasticNetLearner(alpha=alpha,
                                        l1_ratio=1 - self.l2_ratio, **args)
        return learner

    def update_model(self):
        super().update_model()
        coef_table = None
        if self.model is not None:
            domain = Domain(
                [ContinuousVariable("coef")], metas=[StringVariable("name")])
            coefs = list(self.model.coefficients)
            names = [attr.name for attr in self.model.domain.attributes]
            if self.fit_intercept:
                coefs.insert(0, self.model.intercept)
                names.insert(0, "intercept")
            coef_table = Table.from_list(domain, list(zip(coefs, names)))
            coef_table.name = _tr.m[2297, "coefficients"]
        self.Outputs.coefficients.send(coef_table)

    def get_learner_parameters(self):
        regularization = _tr.m[2298, "No Regularization"]
        if self.reg_type == OWLinearRegression.Ridge:
            regularization = (_tr.m[2299, "Ridge Regression (L2) with α={}"]
                              .format(self.alphas[self.alpha_index]))
        elif self.reg_type == OWLinearRegression.Lasso:
            regularization = (_tr.m[2300, "Lasso Regression (L1) with α={}"]
                              .format(self.alphas[self.alpha_index]))
        elif self.reg_type == OWLinearRegression.Elastic:
            regularization = ((_tr.m[2301, "Elastic Net Regression with α={}"] + _tr.m[2302, " and L1:L2 ratio of {}:{}"])
                              .format(self.alphas[self.alpha_index],
                                      self.l2_ratio,
                                      1 - self.l2_ratio))
        return (
            (_tr.m[2303, "Regularization"], regularization),
            (_tr.m[2304, "Fit intercept"], [_tr.m[2305, "No"], _tr.m[2306, "Yes"]][self.fit_intercept])
        )


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWLinearRegression).run(Table("housing"))
