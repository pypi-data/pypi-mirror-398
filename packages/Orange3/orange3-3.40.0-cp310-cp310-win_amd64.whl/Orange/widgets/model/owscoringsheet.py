from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from AnyQt.QtCore import Qt

from Orange.data import Table
from Orange.base import Model
from Orange.widgets.utils.owlearnerwidget import OWBaseLearner
from Orange.widgets.utils.concurrent import TaskState, ConcurrentWidgetMixin
from Orange.widgets.widget import Msg
from Orange.widgets import gui
from Orange.widgets.settings import Setting

from Orange.classification.scoringsheet import ScoringSheetLearner


class ScoringSheetRunner:
    @staticmethod
    def run(learner: ScoringSheetLearner, data: Table, state: TaskState) -> Model:
        if data is None:
            return None
        state.set_status(_tr.m[2477, "Learning..."])
        model = learner(data)
        return model


class OWScoringSheet(OWBaseLearner, ConcurrentWidgetMixin):
    name = _tr.m[2478, "Scoring Sheet"]
    description = _tr.m[2479, "A fast and explainable classifier."]
    icon = "icons/ScoringSheet.svg"
    replaces = ["orangecontrib.prototypes.widgets.owscoringsheet.OWScoringSheet"]
    priority = 75
    keywords = "scoring sheet"

    LEARNER = ScoringSheetLearner

    class Inputs(OWBaseLearner.Inputs):
        pass

    class Outputs(OWBaseLearner.Outputs):
        pass

    # Preprocessing
    num_attr_after_selection = Setting(20)

    # Scoring Sheet Settings
    num_decision_params = Setting(5)
    max_points_per_param = Setting(5)
    custom_features_checkbox = Setting(False)
    num_input_features = Setting(1)

    # Warning messages
    class Information(OWBaseLearner.Information):
        custom_num_of_input_features = Msg(
            (_tr.m[2480, "If the number of input features used is too low for the number of decision \n"] + _tr.m[2481, "parameters, the number of decision parameters will be adjusted to fit the model."])
        )

    def __init__(self):
        ConcurrentWidgetMixin.__init__(self)
        OWBaseLearner.__init__(self)

    def add_main_layout(self):
        box = gui.vBox(self.controlArea, _tr.m[2482, "Preprocessing"])

        self.num_attr_after_selection_spin = gui.spin(
            box,
            self,
            "num_attr_after_selection",
            minv=1,
            maxv=100,
            step=1,
            label=_tr.m[2483, "Number of Attributes After Feature Selection:"],
            orientation=Qt.Horizontal,
            alignment=Qt.AlignRight,
            callback=self.settings_changed,
            controlWidth=45,
        )

        box = gui.vBox(self.controlArea, _tr.m[2484, "Model Parameters"])

        gui.spin(
            box,
            self,
            "num_decision_params",
            minv=1,
            maxv=50,
            step=1,
            label=_tr.m[2485, "Maximum Number of Decision Parameters:"],
            orientation=Qt.Horizontal,
            alignment=Qt.AlignRight,
            callback=self.settings_changed,
            controlWidth=45,
        )

        gui.spin(
            box,
            self,
            "max_points_per_param",
            minv=1,
            maxv=100,
            step=1,
            label=_tr.m[2486, "Maximum Points per Decision Parameter:"],
            orientation=Qt.Horizontal,
            alignment=Qt.AlignRight,
            callback=self.settings_changed,
            controlWidth=45,
        )

        gui.checkBox(
            box,
            self,
            "custom_features_checkbox",
            label=_tr.m[2487, "Custom number of input features"],
            callback=[self.settings_changed, self.custom_input_features],
        )

        self.custom_features = gui.spin(
            box,
            self,
            "num_input_features",
            minv=1,
            maxv=50,
            step=1,
            label=_tr.m[2488, "Number of Input Features Used:"],
            orientation=Qt.Horizontal,
            alignment=Qt.AlignRight,
            callback=self.settings_changed,
            controlWidth=45,
        )

        self.custom_input_features()

    def custom_input_features(self):
        self.custom_features.setEnabled(self.custom_features_checkbox)
        if self.custom_features_checkbox:
            self.Information.custom_num_of_input_features()
        else:
            self.Information.custom_num_of_input_features.clear()
        self.apply()

    @Inputs.data
    def set_data(self, data):
        self.cancel()
        super().set_data(data)

    @Inputs.preprocessor
    def set_preprocessor(self, preprocessor):
        self.cancel()
        super().set_preprocessor(preprocessor)

        # Enable or disable the spin box based on whether a preprocessor is set
        self.num_attr_after_selection_spin.setEnabled(preprocessor is None)
        if preprocessor:
            self.Information.ignored_preprocessors()
        else:
            self.Information.ignored_preprocessors.clear()

    def create_learner(self):
        return self.LEARNER(
            num_attr_after_selection=self.num_attr_after_selection,
            num_decision_params=self.num_decision_params,
            max_points_per_param=self.max_points_per_param,
            num_input_features=(
                self.num_input_features if self.custom_features_checkbox else None
            ),
            preprocessors=self.preprocessors,
        )

    def update_model(self):
        self.cancel()
        self.show_fitting_failed(None)
        self.model = None
        if self.data is not None:
            self.start(ScoringSheetRunner.run, self.learner, self.data)
        else:
            self.Outputs.model.send(None)

    def get_learner_parameters(self):
        return (
            self.num_decision_params,
            self.max_points_per_param,
            self.num_input_features,
        )

    def on_partial_result(self, _):
        pass

    def on_done(self, result: Model):
        assert isinstance(result, Model) or result is None
        self.model = result
        self.Outputs.model.send(result)

    def on_exception(self, ex):
        self.cancel()
        self.Outputs.model.send(None)
        if isinstance(ex, BaseException):
            self.show_fitting_failed(ex)

    def onDeleteWidget(self):
        self.shutdown()
        super().onDeleteWidget()


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(OWScoringSheet).run()
