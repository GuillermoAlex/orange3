import os, sys

from PyQt4 import QtGui, QtCore

from Orange.misc import DistMatrix
from Orange.widgets import widget, gui
from Orange.data import get_sample_datasets_dir
from Orange.widgets.utils.filedialogs import RecentPathsWidgetMixin


class OWDistanceFile(widget.OWWidget, RecentPathsWidgetMixin):
    name = "Distance File"
    id = "orange.widgets.unsupervised.distancefile"
    description = "Read distances from file"
    icon = "icons/DistanceFile.svg"
    priority = 10
    category = "Data"
    keywords = ["data", "distances", "load", "read"]
    outputs = [("Distances", DistMatrix)]

    want_main_area = False
    resizing_enabled = False

    # recent_paths = Setting([]) comes from RecentPathsWidgetMixin

    def __init__(self):
        super().__init__()
        RecentPathsWidgetMixin.__init__(self)
        self.loaded_file = ""

        vbox = gui.vBox(self.controlArea, "Distance File", addSpace=True)
        box = gui.hBox(vbox)
        self.file_combo = QtGui.QComboBox(box)
        self.file_combo.setMinimumWidth(300)
        box.layout().addWidget(self.file_combo)
        self.file_combo.activated[int].connect(self.select_file)

        button = gui.button(box, self, '...', callback=self.browse_file)
        button.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DirOpenIcon))
        button.setSizePolicy(
            QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)

        button = gui.button(
            box, self, "Reload", callback=self.reload, default=True)
        button.setIcon(self.style().standardIcon(QtGui.QStyle.SP_BrowserReload))
        button.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        box = gui.vBox(self.controlArea, "Info", addSpace=True)
        self.infoa = gui.widgetLabel(box, 'No data loaded.')
        self.warnings = gui.widgetLabel(box, ' ')
        #Set word wrap, so long warnings won't expand the widget
        self.warnings.setWordWrap(True)
        self.warnings.setSizePolicy(
            QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.MinimumExpanding)

        self.set_file_list()
        QtCore.QTimer.singleShot(0, self.open_file)

    def set_file_list(self):
        super().set_file_list()
        self.file_combo.addItem("Browse documentation data sets...")

    def reload(self):
        return self.open_file()

    def select_file(self, n):
        if n < len(self.recent_paths) :
            name = self.recent_paths[n]
            del self.recent_paths[n]
            self.recent_paths.insert(0, name)
        elif n:
            self.browse_file(True)

        self.set_file_list()
        self.open_file()

    def browse_file(self, in_demos=0):
        if in_demos:
            try:
                start_file = get_sample_datasets_dir()
            except AttributeError:
                start_file = ""
            if not start_file or not os.path.exists(start_file):
                widgets_dir = os.path.dirname(gui.__file__)
                orange_dir = os.path.dirname(widgets_dir)
                start_file = os.path.join(orange_dir, "doc", "datasets")
            if not start_file or not os.path.exists(start_file):
                d = os.getcwd()
                if os.path.basename(d) == "canvas":
                    d = os.path.dirname(d)
                start_file = os.path.join(os.path.dirname(d), "doc", "datasets")
            if not os.path.exists(start_file):
                QtGui.QMessageBox.information(
                    None, "File",
                    "Cannot find the directory with example files")
                return
        else:
            if self.recent_paths and self.recent_paths[0].abspath != "(none)":
                start_file = self.recent_paths[0]
            else:
                start_file = os.path.expanduser("~/")

        filename = QtGui.QFileDialog.getOpenFileName(
            self, 'Open Distance File', start_file)
        if not filename:
            return
        self.add_path(filename)
        self.set_file_list()
        self.open_file()

    # Open a file, create data from it and send it over the data channel
    def open_file(self):
        self.error()
        self.warning()
        self.information()

        if not self.recent_paths or self.recent_paths[0].abspath == "(none)":
            return
        fn = self.recent_paths[0].abspath
        if not os.path.exists(fn):
            dir_name, basename = os.path.split(fn)
            if os.path.exists(os.path.join(".", basename)):
                fn = os.path.join(".", basename)
                self.information("Loading '{}' from the current directory."
                                 .format(basename))
        if fn == "(none)":
            self.send("Distances", None)
            self.infoa.setText("No data loaded")
            self.infob.setText("")
            self.warnings.setText("")
            return

        self.loaded_file = ""

        try:
            distances = DistMatrix.from_file(fn)
            self.loaded_file = fn
        except Exception as exc:
            err_value = str(exc)
            self.error("Invalid file format")
            self.infoa.setText('Data was not loaded due to an error.')
            self.warnings.setText(err_value)
            distances = None

        if distances is not None:
            self.infoa.setText(
                "{} points(s), ".format(len(distances)) +
                (["unlabelled", "labelled"][distances.row_items is not None]))
            self.warnings.setText("")
            file_name = os.path.split(fn)[1]
            if "." in file_name:
                distances.name = file_name[:file_name.rfind('.')]
            else:
                distances.name = file_name

        self.send("Distances", distances)

    def sendReport(self):
        if self.loaded_file:
            self.reportSettings("File", [("File name", self.loaded_file)])

if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = OWDistanceFile()
    ow.show()
    a.exec_()
    ow.saveSettings()
