from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
import os

import numpy as np

from AnyQt.QtWidgets import QSizePolicy, QStyle, QMessageBox, QFileDialog
from AnyQt.QtCore import QTimer, QUrl

from orangewidget.settings import Setting
from orangewidget.widget import Msg
from orangewidget.workflow.drophandler import SingleFileDropHandler

from Orange.misc import DistMatrix
from Orange.widgets import widget, gui
from Orange.data import get_sample_datasets_dir
from Orange.widgets.utils.filedialogs import RecentPathsWComboMixin, RecentPath, \
    stored_recent_paths_prepend, OWUrlDropBase
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Output


class OWDistanceFile(OWUrlDropBase, RecentPathsWComboMixin):
    name = _tr.m[2676, "Distance File"]
    id = "orange.widgets.unsupervised.distancefile"
    description = _tr.m[2677, "Read distances from a file."]
    icon = "icons/DistanceFile.svg"
    priority = 10
    keywords = _tr.m[2678, "distance file, load, read, open"]

    class Outputs:
        distances = Output(_tr.m[2679, "Distances"], DistMatrix, dynamic=False)

    class Error(widget.OWWidget.Error):
        invalid_file = Msg(_tr.m[2680, "Data was not loaded:{}"])
        non_square_matrix = Msg(
            (_tr.m[2681, "Matrix is not square. "] + _tr.m[2682, "Reformat the file and use the File widget to read it."]))

    want_main_area = False
    resizing_enabled = False

    auto_symmetric = Setting(True)

    def __init__(self):
        super().__init__()
        RecentPathsWComboMixin.__init__(self)
        self.distances = None

        vbox = gui.vBox(self.controlArea, _tr.m[2683, "Distance File"])
        box = gui.hBox(vbox)
        self.file_combo.setMinimumWidth(300)
        box.layout().addWidget(self.file_combo)
        self.file_combo.activated[int].connect(self.select_file)

        button = gui.button(box, self, '...', callback=self.browse_file)
        button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        button.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Fixed)

        button = gui.button(
            box, self, _tr.m[2684, "Reload"], callback=self.reload, default=True)
        button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        vbox = gui.vBox(self.controlArea, _tr.m[2685, "Options"])
        gui.checkBox(
            vbox, self, "auto_symmetric",
            _tr.m[2686, "Treat triangular matrices as symmetric"],
            tooltip=(_tr.m[2687, "If matrix is triangular, this will copy the data to the "] + _tr.m[2688, "other triangle"]),
            callback=self.commit
        )

        gui.rubber(self.buttonsArea)
        gui.button(
            self.buttonsArea, self, _tr.m[2689, "Browse documentation datasets"],
            callback=lambda: self.browse_file(True), autoDefault=False)
        gui.rubber(self.buttonsArea)

        self.set_file_list()
        QTimer.singleShot(0, self.open_file)

    def reload(self):
        return self.open_file()

    def select_file(self, n):
        super().select_file(n)
        self.set_file_list()
        self.open_file()

    def browse_file(self, in_demos=False):
        if in_demos:
            start_file = get_sample_datasets_dir()
            if not os.path.exists(start_file):
                QMessageBox.information(
                    None, _tr.m[2690, "File"],
                    _tr.m[2691, "Cannot find the directory with documentation datasets"])
                return
        else:
            start_file = self.last_path() or os.path.expanduser("~/")

        filename, _ = QFileDialog.getOpenFileName(
            self, _tr.m[2692, 'Open Distance File'], start_file,
            (_tr.m[2693, "All Readable Files (*.xlsx *.dst);;"] + (_tr.m[2694, "Excel File (*.xlsx);;"] + _tr.m[2695, "Distance File (*.dst)"])))
        if not filename:
            return
        self.add_path(filename)
        self.open_file()

    def open_file(self):
        self.Error.clear()
        self.distances = None
        fn = self.last_path()
        if fn and not os.path.exists(fn):
            dir_name, basename = os.path.split(fn)
            if os.path.exists(os.path.join(".", basename)):
                fn = os.path.join(".", basename)
        if fn and fn != _tr.m[2696, "(none)"]:
            try:
                distances = DistMatrix.from_file(fn)
            except Exception as exc:
                err = str(exc)
                self.Error.invalid_file(" \n"[len(err) > 40] + err)
            else:
                if distances.shape[0] != distances.shape[1]:
                    self.Error.non_square_matrix()
                else:
                    np.nan_to_num(distances)
                    self.distances = distances
                    _, filename = os.path.split(fn)
                    self.distances.name, _ = os.path.splitext(filename)
        self.commit()

    def commit(self):
        distances = self.distances
        if distances is not None:
            if self.auto_symmetric:
                distances = distances.auto_symmetricized()
            if np.any(np.isnan(distances)):
                distances = np.nan_to_num(distances)
        self.Outputs.distances.send(distances)

    def send_report(self):
        if not self.distances:
            self.report_paragraph(_tr.m[2697, "No data was loaded."])
        else:
            self.report_items([(_tr.m[2698, "File name"], self.distances.name)])

    def canDropUrl(self, url: QUrl) -> bool:
        if url.isLocalFile():
            return OWDistanceFileDropHandler().canDropFile(url.toLocalFile())
        else:
            return False

    def handleDroppedUrl(self, url: QUrl) -> None:
        if url.isLocalFile():
            self.add_path(url.toLocalFile())
            self.open_file()


class OWDistanceFileDropHandler(SingleFileDropHandler):
    WIDGET = OWDistanceFile

    def parametersFromFile(self, path):
        r = RecentPath(os.path.abspath(path), None, None,
                       os.path.basename(path))
        return {"recent_paths": stored_recent_paths_prepend(self.WIDGET, r)}

    def canDropFile(self, path: str) -> bool:
        return os.path.splitext(path)[1].lower() in (".dst", ".xlsx")


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWDistanceFile).run()
