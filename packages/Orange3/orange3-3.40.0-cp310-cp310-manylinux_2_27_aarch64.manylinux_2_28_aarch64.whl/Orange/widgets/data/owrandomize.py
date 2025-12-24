from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
import random

from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QSizePolicy

from Orange.data import Table
from Orange.preprocess import Randomize
from Orange.widgets.settings import Setting
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui


class OWRandomize(OWWidget):
    name = _tr.m[1417, "Randomize"]
    description = _tr.m[1418, "Randomize features, class and/or metas in data table."]
    category = _tr.m[1419, "Transform"]
    icon = "icons/Random.svg"
    priority = 2200
    keywords = _tr.m[1420, "randomize, random"]

    class Inputs:
        data = Input(_tr.m[1421, "Data"], Table)

    class Outputs:
        data = Output(_tr.m[1422, "Data"], Table)

    resizing_enabled = False
    want_main_area = False

    shuffle_class = Setting(True)
    shuffle_attrs = Setting(False)
    shuffle_metas = Setting(False)
    scope_prop = Setting(80)
    random_seed = Setting(False)
    auto_apply = Setting(True)

    def __init__(self):
        super().__init__()
        self.data = None

        # GUI
        box = gui.hBox(self.controlArea, _tr.m[1423, "Shuffled columns"])
        box.layout().setSpacing(20)
        self.class_check = gui.checkBox(
            box, self, "shuffle_class", _tr.m[1424, "Classes"],
            callback=self._shuffle_check_changed)
        self.attrs_check = gui.checkBox(
            box, self, "shuffle_attrs", _tr.m[1425, "Features"],
            callback=self._shuffle_check_changed)
        self.metas_check = gui.checkBox(
            box, self, "shuffle_metas", _tr.m[1426, "Metas"],
            callback=self._shuffle_check_changed)

        box = gui.vBox(self.controlArea, _tr.m[1427, "Shuffled rows"])
        hbox = gui.hBox(box)
        gui.widgetLabel(hbox, _tr.m[1428, "None"])
        self.scope_slider = gui.hSlider(
            hbox, self, "scope_prop", minValue=0, maxValue=100, width=140,
            createLabel=False, callback=self._scope_slider_changed)
        gui.widgetLabel(hbox, _tr.m[1429, "All"])
        self.scope_label = gui.widgetLabel(
            box, "", alignment=Qt.AlignCenter,
            sizePolicy=(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self._set_scope_label()
        self.replicable_check = gui.checkBox(
            box, self, "random_seed", _tr.m[1430, "Replicable shuffling"],
            callback=self._shuffle_check_changed)

        gui.auto_apply(self.buttonsArea, self)

    @property
    def parts(self):
        return [self.shuffle_class, self.shuffle_attrs, self.shuffle_metas]

    def _shuffle_check_changed(self):
        self.commit.deferred()

    def _scope_slider_changed(self):
        self._set_scope_label()
        self.commit.deferred()

    def _set_scope_label(self):
        self.scope_label.setText("{}%".format(self.scope_prop))

    @Inputs.data
    def set_data(self, data):
        self.data = data
        self.commit.now()

    @gui.deferred
    def commit(self):
        data = None
        if self.data:
            rand_seed = self.random_seed or None
            size = int(len(self.data) * self.scope_prop / 100)
            random.seed(rand_seed)
            indices = sorted(random.sample(range(len(self.data)), size))
            type_ = sum(t for t, p in zip(Randomize.Type, self.parts) if p)
            randomized = Randomize(type_, rand_seed)(self.data[indices])
            data = self.data.copy()
            with data.unlocked():
                for i, instance in zip(indices, randomized):
                    data[i] = instance
        self.Outputs.data.send(data)

    def send_report(self):
        labels = [_tr.m[1431, "classes"], _tr.m[1432, "features"], _tr.m[1433, "metas"]]
        include = [label for label, i in zip(labels, self.parts) if i]
        text = _tr.m[1434, "none"] if not include else \
            _tr.m[1435, " and "].join(filter(None, (", ".join(include[:-1]), include[-1])))
        self.report_items(
            _tr.m[1436, "Settings"],
            [(_tr.m[1437, "Shuffled columns"], text),
             (_tr.m[1438, "Proportion of shuffled rows"], "{}%".format(self.scope_prop)),
             (_tr.m[1439, "Replicable"], _tr.m[1440, "yes"] if self.random_seed else _tr.m[1441, "no"])])


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWRandomize).run(Table("iris"))
