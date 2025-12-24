from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
import numpy as np

from AnyQt.QtCore import Qt

from Orange.data import Table, Domain, ContinuousVariable
from Orange.data.util import get_unique_names
from Orange.preprocess import RemoveNaNColumns, Impute
from Orange import distance
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Orange.widgets.utils.signals import Input, Output
from Orange.widgets.widget import OWWidget, Msg
from Orange.widgets.utils.widgetpreview import WidgetPreview

METRICS = [
    (_tr.m[1085, "Euclidean"], distance.Euclidean),
    (_tr.m[1086, "Manhattan"], distance.Manhattan),
    (_tr.m[1087, "Mahalanobis"], distance.Mahalanobis),
    (_tr.m[1088, "Cosine"], distance.Cosine),
    (_tr.m[1089, "Jaccard"], distance.Jaccard),
    (_tr.m[1090, "Spearman"], distance.SpearmanR),
    (_tr.m[1091, "Absolute Spearman"], distance.SpearmanRAbsolute),
    (_tr.m[1092, "Pearson"], distance.PearsonR),
    (_tr.m[1093, "Absolute Pearson"], distance.PearsonRAbsolute),
]


class OWNeighbors(OWWidget):
    name = _tr.m[1094, "Neighbors"]
    description = _tr.m[1095, "Compute nearest neighbors in data according to reference."]
    icon = "icons/Neighbors.svg"
    category = _tr.m[1096, "Unsupervised"]
    replaces = ["orangecontrib.prototypes.widgets.owneighbours.OWNeighbours"]

    class Inputs:
        data = Input(_tr.m[1097, "Data"], Table)
        reference = Input(_tr.m[1098, "Reference"], Table)

    class Outputs:
        data = Output(_tr.m[1099, "Neighbors"], Table)

    class Info(OWWidget.Warning):
        removed_references = \
            Msg((_tr.m[1100, "Input data includes reference instance(s).\n"] + _tr.m[1101, "Reference instances are not considered as neighbours."]))

    class Warning(OWWidget.Warning):
        all_data_as_reference = \
            Msg(_tr.m[1102, "Every data instance is same as some reference"])

    class Error(OWWidget.Error):
        diff_domains = Msg(_tr.m[1103, "Data and reference have different features"])

    n_neighbors: int
    distance_index: int

    n_neighbors = Setting(10)
    limit_neighbors = Setting(True)
    distance_index = Setting(0)
    include_reference = Setting(False)
    auto_apply = Setting(True)

    want_main_area = False
    resizing_enabled = False

    def __init__(self):
        super().__init__()

        self.data = None
        self.reference = None
        self.distances = None

        box = gui.vBox(self.controlArea, box=True)
        gui.comboBox(
            box, self, "distance_index", orientation=Qt.Horizontal,
            label=_tr.m[1104, "Distance metric: "], items=[d[0] for d in METRICS],
            callback=self.recompute)
        gui.spin(
            box, self, "n_neighbors", label=_tr.m[1105, "Limit number of neighbors to:"],
            step=1, spinType=int, minv=0, maxv=100, checked='limit_neighbors',
            # call apply by gui.auto_commit, pylint: disable=unnecessary-lambda
            checkCallback=self.commit.deferred,
            callback=self.commit.deferred)
        gui.checkBox(
            box, self, "include_reference", label=_tr.m[1106, "Include reference example"],
            callback=self.commit.deferred
        )

        self.apply_button = gui.auto_apply(self.buttonsArea, self)

    @Inputs.data
    def set_data(self, data):
        self.controls.n_neighbors.setMaximum(len(data) if data else 100)
        self.data = data

    @Inputs.reference
    def set_ref(self, refs):
        self.reference = refs

    def handleNewSignals(self):
        self.compute_distances()
        self.commit.now()

    def recompute(self):
        self.compute_distances()
        self.commit.deferred()

    def compute_distances(self):
        self.Error.diff_domains.clear()
        if not self.data or not self.reference:
            self.distances = None
            return
        if set(self.reference.domain.attributes) != \
                set(self.data.domain.attributes):
            self.Error.diff_domains()
            self.distances = None
            return

        metric = METRICS[self.distance_index][1]
        n_ref = len(self.reference)

        # comparing only attributes, no metas and class-vars
        new_domain = Domain(self.data.domain.attributes)
        reference = self.reference.transform(new_domain)
        data = self.data.transform(new_domain)

        all_data = Table.concatenate([reference, data], 0)
        pp_all_data = Impute()(RemoveNaNColumns()(all_data))
        pp_reference, pp_data = pp_all_data[:n_ref], pp_all_data[n_ref:]
        self.distances = metric(pp_data, pp_reference).min(axis=1)

    @gui.deferred
    def commit(self):
        indices = self._compute_indices()

        if indices is None:
            neighbors = None
        else:
            neighbors = self._data_with_similarity(indices)
            neighbors.name = self.data.name + _tr.m[1107, " (neighbors)"]
        self.Outputs.data.send(neighbors)

    def _compute_indices(self):
        self.Warning.all_data_as_reference.clear()
        self.Info.removed_references.clear()

        if self.distances is None:
            return None

        inrefs = np.isin(self.data.ids, self.reference.ids)
        if np.all(inrefs):
            self.Warning.all_data_as_reference()
            return None
        if np.any(inrefs):
            self.Info.removed_references()

        dist = np.copy(self.distances)
        dist[inrefs] = np.max(dist) + 1
        up_to = len(dist) - np.sum(inrefs)
        if self.limit_neighbors and self.n_neighbors < up_to:
            up_to = self.n_neighbors
        # get indexes of N neighbours in unsorted order - faster than argsort
        idx = np.argpartition(dist, up_to - 1)[:up_to]
        # sort selected N neighbours according to distances
        sorted_subset_idx = np.argsort(dist[idx])
        # map sorted indexes back to original index space
        return idx[sorted_subset_idx]

    def _data_with_similarity(self, indices):
        domain = self.data.domain
        dist_var = ContinuousVariable(get_unique_names(domain, "distance"))
        metas = domain.metas + (dist_var, )
        domain = Domain(domain.attributes, domain.class_vars, metas)
        neighbours = self.data.from_table(domain, self.data, row_indices=indices)
        distances = self.distances[indices]
        if self.include_reference:
            neighbours = Table.concatenate(
                [neighbours,
                 self.reference.transform(neighbours.domain)])
            distances = np.hstack(
                (distances,
                 [np.nan] * len(self.reference)))
        with neighbours.unlocked(neighbours.metas):
            if distances.size > 0:
                neighbours.set_column(dist_var, distances)
        return neighbours


if __name__ == "__main__":  # pragma: no cover
    iris = Table("iris.tab")
    WidgetPreview(OWNeighbors).run(
        set_data=iris,
        set_ref=iris[:1])
