from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from itertools import chain

from AnyQt.QtWidgets import QComboBox, QCheckBox

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Msg

from Orange.data import Variable, Table
from Orange.modelling.column import (
    ColumnModel, ColumnLearner, valid_value_sets, valid_prob_range)
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets.utils.itemmodels import VariableListModel
from Orange.widgets.utils.widgetpreview import WidgetPreview


class OWFeatureAsPredictor(OWWidget):
    name = _tr.m[1883, "Feature as Predictor"]
    description = _tr.m[1884, "Use a column as probabilities or predictions"]
    icon = "icons/FeatureAsPredictor.svg"
    priority = 1000
    keywords = "column predictor"

    want_main_area = False
    resizing_enabled = False

    class Inputs:
        data = Input(_tr.m[1885, "Data"], Table)

    class Outputs:
        learner = Output(_tr.m[1886, "Learner"], ColumnLearner)
        model = Output(_tr.m[1887, "Model"], ColumnModel)

    class Error(OWWidget.Error):
        no_class = Msg(_tr.m[1888, "Data has no target variable."])
        no_variables = Msg(_tr.m[1889, "No useful variables"])

    column_hint: Variable = Setting(None, schema_only=True)
    # Stores the last user setting.
    # apply_transformation tells what will actually happens;
    # checkbox may be disabled and set to reflect apply_transformation.
    apply_transformation_setting = Setting(False)
    auto_apply = Setting(True)

    def __init__(self):
        super().__init__()
        self.data = None
        self.column = None
        self.apply_transformation = False
        self.pars_to_report = (False, False)

        box = gui.vBox(self.controlArea, True)

        self.column_combo = combo = QComboBox()
        combo.setModel(VariableListModel())
        box.layout().addWidget(combo)
        @combo.activated.connect
        def on_column_changed(index):
            self.column = combo.model()[index]
            self.column_hint = self.column.name
            self._update_controls()
            self.commit.deferred()

        self.cb_transformation = cb = QCheckBox("", self)
        box.layout().addWidget(cb)
        @cb.clicked.connect
        def on_apply_transformation_changed(checked):
            self.apply_transformation_setting \
                = self.apply_transformation = checked
            self.commit.deferred()

        gui.auto_apply(self.controlArea, self, "auto_apply")
        self._update_controls()

    def _update_controls(self):
        cb = self.cb_transformation
        data = self.data

        if data is None or self.column is None:
            cb.setChecked(self.apply_transformation_setting)
            cb.setDisabled(False)
            return

        if self.column.is_discrete:
            self.apply_transformation = False
            cb.setChecked(False)
            cb.setDisabled(True)
        elif (data.domain.class_var.is_discrete
                and not valid_prob_range(data.get_column(self.column))):
            self.apply_transformation = True
            cb.setChecked(True)
            cb.setDisabled(True)
        else:
            self.apply_transformation = self.apply_transformation_setting
            cb.setChecked(self.apply_transformation_setting)
            cb.setDisabled(False)

        shape = _tr.m[1890, "logistic"] if data.domain.class_var.is_discrete else _tr.m[1891, "linear"]
        cb.setText(_tr.e(_tr.c(1892, f"Transform through {shape} function")))
        cb.setToolTip(_tr.e(_tr.c(1893, f"Use {shape} regression to fit the model's coefficients")))

    @Inputs.data
    def set_data(self, data):
        self._set_data(data)
        self._update_controls()
        self.commit.now()

    def _set_data(self, data):
        column_model: VariableListModel = self.column_combo.model()

        self.Error.clear()
        column_model.clear()
        self.column = None
        self.data = None

        if data is None:
            return

        class_var = data.domain.class_var
        if class_var is None:
            self.Error.no_class()
            return

        allow_continuous = (class_var.is_continuous
                            or len(class_var.values) == 2)
        column_model[:] = (
            var
            for var in chain(data.domain.attributes, data.domain.metas)
            if (var.is_continuous and allow_continuous
                or (var.is_discrete and class_var.is_discrete
                    and valid_value_sets(class_var, var))
                )
        )
        if not column_model:
            self.Error.no_variables()
            return

        self.data = data
        if self.column_hint \
                and self.column_hint in self.data.domain \
                and (var := self.data.domain[self.column_hint]) in column_model:
            self.column = var
            self.column_combo.setCurrentIndex(column_model.indexOf(self.column))
        else:
            self.column = column_model[0]
            self.column_combo.setCurrentIndex(0)
            self.column_hint = self.column.name

    @gui.deferred
    def commit(self):
        self.pars_to_report = (False, False)
        if self.column is None:
            self.Outputs.learner.send(None)
            self.Outputs.model.send(None)
            return

        learner = ColumnLearner(
            self.data.domain.class_var, self.column, self.apply_transformation)
        model = learner(self.data)
        self.Outputs.learner.send(learner)
        self.Outputs.model.send(model)
        if self.apply_transformation:
            self.pars_to_report = (model.intercept, model.coefficient)

    def send_report(self):
        if self.column is None:
            return
        self.report_items((
            (_tr.m[1894, "Predict values from"], self.column.name),
            (_tr.m[1895, "Applied transformation"],
             self.apply_transformation and self.data is not None and
             (_tr.m[1896, "logistic"] if self.data.domain.class_var.is_discrete else _tr.m[1897, "linear"])),
            (_tr.m[1898, "Intercept"], self.pars_to_report[0]),
            (_tr.m[1899, "Coefficient"], self.pars_to_report[1])
        ))


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWFeatureAsPredictor).run(Table("heart_disease"))
