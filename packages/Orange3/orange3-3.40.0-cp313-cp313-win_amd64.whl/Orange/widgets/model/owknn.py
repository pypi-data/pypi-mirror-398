from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from AnyQt.QtCore import Qt

from Orange.data import Table
from Orange.modelling import KNNLearner
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.utils.owlearnerwidget import OWBaseLearner
from Orange.widgets.utils.widgetpreview import WidgetPreview


class OWKNNLearner(OWBaseLearner):
    name = _tr.m[2266, "kNN"]
    description = _tr.m[2267, "Predict according to the nearest training instances."]
    icon = "icons/KNN.svg"
    replaces = [
        "Orange.widgets.classify.owknn.OWKNNLearner",
        "Orange.widgets.regression.owknnregression.OWKNNRegression",
    ]
    priority = 20
    keywords = _tr.m[2268, "knn, k nearest, knearest, neighbor, neighbour"]

    LEARNER = KNNLearner

    weights = ["uniform", "distance"]
    metrics = ["euclidean", "manhattan", "chebyshev", "mahalanobis"]

    weights_options = [_tr.m[2269, "Uniform"], _tr.m[2270, "By Distances"]]
    metrics_options = [_tr.m[2271, "Euclidean"], _tr.m[2272, "Manhattan"], _tr.m[2273, "Chebyshev"], _tr.m[2274, "Mahalanobis"]]

    n_neighbors = Setting(5)
    metric_index = Setting(0)
    weight_index = Setting(0)

    def add_main_layout(self):
        # this is part of init, pylint: disable=attribute-defined-outside-init
        box = gui.vBox(self.controlArea, _tr.m[2275, "Neighbors"])
        self.n_neighbors_spin = gui.spin(
            box, self, "n_neighbors", 1, 100, label=_tr.m[2276, "Number of neighbors:"],
            alignment=Qt.AlignRight, callback=self.settings_changed,
            controlWidth=80)
        self.metrics_combo = gui.comboBox(
            box, self, "metric_index", orientation=Qt.Horizontal,
            label=_tr.m[2277, "Metric:"], items=self.metrics_options,
            callback=self.settings_changed)
        self.weights_combo = gui.comboBox(
            box, self, "weight_index", orientation=Qt.Horizontal,
            label=_tr.m[2278, "Weight:"], items=self.weights_options,
            callback=self.settings_changed)

    def create_learner(self):
        return self.LEARNER(
            n_neighbors=self.n_neighbors,
            metric=self.metrics[self.metric_index],
            weights=self.weights[self.weight_index],
            preprocessors=self.preprocessors)

    def get_learner_parameters(self):
        return ((_tr.m[2279, "Number of neighbours"], self.n_neighbors),
                (_tr.m[2280, "Metric"], self.metrics_options[self.metric_index]),
                (_tr.m[2281, "Weight"], self.weights_options[self.weight_index]))


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWKNNLearner).run(Table("iris"))
