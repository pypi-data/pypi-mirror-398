"""Tree learner widget"""
from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator

from collections import OrderedDict

from AnyQt.QtCore import Qt

from Orange.data import Table
from Orange.modelling.tree import TreeLearner
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.utils.localization import pl
from Orange.widgets.utils.owlearnerwidget import OWBaseLearner
from Orange.widgets.utils.widgetpreview import WidgetPreview


class OWTreeLearner(OWBaseLearner):
    """Tree algorithm with forward pruning."""
    name = _tr.m[2573, "Tree"]
    description = _tr.m[2574, "A tree algorithm with forward pruning."]
    icon = "icons/Tree.svg"
    replaces = [
        "Orange.widgets.classify.owclassificationtree.OWClassificationTree",
        "Orange.widgets.regression.owregressiontree.OWRegressionTree",
        "Orange.widgets.classify.owclassificationtree.OWTreeLearner",
        "Orange.widgets.regression.owregressiontree.OWTreeLearner",
    ]
    priority = 30
    keywords = _tr.m[2575, "tree, classification tree"]

    LEARNER = TreeLearner

    binary_trees = Setting(True)
    limit_min_leaf = Setting(True)
    min_leaf = Setting(2)
    limit_min_internal = Setting(True)
    min_internal = Setting(5)
    limit_depth = Setting(True)
    max_depth = Setting(100)

    # Classification only settings
    limit_majority = Setting(True)
    sufficient_majority = Setting(95)

    spin_boxes = (
        (_tr.m[2576, "Min. number of instances in leaves: "],
         "limit_min_leaf", "min_leaf", 1, 1000),
        (_tr.m[2577, "Do not split subsets smaller than: "],
         "limit_min_internal", "min_internal", 1, 1000),
        (_tr.m[2578, "Limit the maximal tree depth to: "],
         "limit_depth", "max_depth", 1, 1000))

    classification_spin_boxes = (
        (_tr.m[2579, "Stop when majority reaches [%]: "],
         "limit_majority", "sufficient_majority", 51, 100),)

    def add_main_layout(self):
        box = gui.widgetBox(self.controlArea, _tr.m[2580, 'Parameters'])
        # the checkbox is put into vBox for alignemnt with other checkboxes
        gui.checkBox(box, self, "binary_trees", _tr.m[2581, "Induce binary tree"],
                     callback=self.settings_changed,
                     attribute=Qt.WA_LayoutUsesWidgetRect)
        for label, check, setting, fromv, tov in self.spin_boxes:
            gui.spin(box, self, setting, fromv, tov, label=label,
                     checked=check, alignment=Qt.AlignRight,
                     callback=self.settings_changed,
                     checkCallback=self.settings_changed, controlWidth=80)

    def add_classification_layout(self, box):
        for label, check, setting, minv, maxv in self.classification_spin_boxes:
            gui.spin(box, self, setting, minv, maxv,
                     label=label, checked=check, alignment=Qt.AlignRight,
                     callback=self.settings_changed, controlWidth=80,
                     checkCallback=self.settings_changed)

    def learner_kwargs(self):
        # Pylint doesn't get our Settings
        # pylint: disable=invalid-sequence-index
        return dict(
            max_depth=(None, self.max_depth)[self.limit_depth],
            min_samples_split=(2, self.min_internal)[self.limit_min_internal],
            min_samples_leaf=(1, self.min_leaf)[self.limit_min_leaf],
            binarize=self.binary_trees,
            preprocessors=self.preprocessors,
            sufficient_majority=(1, self.sufficient_majority / 100)[
                self.limit_majority])

    def create_learner(self):
        # pylint: disable=not-callable
        return self.LEARNER(**self.learner_kwargs())

    def get_learner_parameters(self):
        from Orange.widgets.report import plural_w
        items = OrderedDict()
        items[_tr.m[2582, "Pruning"]] = ", ".join(s for s, c in (
            ((_tr.e(_tr.c(2583, f'at least {self.min_leaf} ')) + _tr.e(_tr.c(2584, f'{pl(self.min_leaf, "instance")} in leaves'))),
             self.limit_min_leaf),
            ((_tr.e(_tr.c(2585, f'at least {self.min_internal} ')) + _tr.e(_tr.c(2586, f'{pl(self.min_internal, "instance")} in internal nodes'))),
             self.limit_min_internal),
            (_tr.e(_tr.c(2587, f'maximum depth {self.max_depth}')),
             self.limit_depth)
        ) if c) or _tr.m[2588, "None"]
        if self.limit_majority:
            items[_tr.m[2589, "Splitting"]] = (_tr.m[2590, "Stop splitting when majority reaches %d%% "] + _tr.m[2591, "(classification only)"]) % \
                                 self.sufficient_majority
        items[_tr.m[2592, "Binary trees"]] = (_tr.m[2593, "No"], _tr.m[2594, "Yes"])[self.binary_trees]
        return items


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWTreeLearner).run(Table("iris"))
