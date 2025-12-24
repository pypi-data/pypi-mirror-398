from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
import pickle

from Orange.widgets.widget import Input
from Orange.base import Model
from Orange.widgets.utils.save.owsavebase import OWSaveBase
from Orange.widgets.utils.widgetpreview import WidgetPreview


class OWSaveModel(OWSaveBase):
    name = _tr.m[2473, "Save Model"]
    description = _tr.m[2474, "Save a trained model to an output file."]
    icon = "icons/SaveModel.svg"
    replaces = ["Orange.widgets.classify.owsaveclassifier.OWSaveClassifier"]
    priority = 3000
    keywords = _tr.m[2475, "save model, save"]

    class Inputs:
        model = Input("Model", Model)

    filters = [_tr.m[2476, "Pickled model (*.pkcls)"]]

    @Inputs.model
    def set_model(self, model):
        self.data = model
        self.on_new_input()

    def do_save(self):
        with open(self.filename, "wb") as f:
            pickle.dump(self.data, f)


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWSaveModel).run()
