from PySide6.QtCore import Qt
from PySide6.QtCore import Slot
from PySide6.QtCore import QThread
from PySide6.QtCore import Signal

from PySide6.QtGui import QAction
from PySide6.QtGui import QIcon

from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QToolBar
from PySide6.QtWidgets import QDockWidget
from PySide6.QtWidgets import QProgressBar

from pathlib import Path

from mimetica import conf
from mimetica import Canvas
from mimetica import Dock
from mimetica import SplitView
from mimetica import Stack


class Tab(QMainWindow):
    load_stack = Signal()

    def __init__(
        self,
        paths: list[Path],
    ):
        QMainWindow.__init__(self)

        self.paths = paths

        # The display canvas
        # ==================================================
        self.canvas = Canvas()

        # Splitview widget
        # ==================================================
        self.splitview = SplitView(self.canvas)
        self.splitview.setSizes((2, 1))
        self.setCentralWidget(self.splitview)

        # Dock
        # ==================================================
        self.dock = Dock(features=QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)

        # Toolbar
        # ==================================================
        self.toolbar = QToolBar(floatable=False, movable=False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # Thread for preventing the GUI from blocking
        # ==================================================
        self.worker = QThread()
        self.worker.start()

        # The layer stack
        # ==================================================
        # logger.info(f'Loading stack | TID: {threading.get_ident()}')
        self.stack = Stack(paths, conf.show_inactive_plots)
        self.load_stack.connect(self.stack.process)
        self.stack.set_canvas.connect(self.set_canvas)
        self.stack.abort.connect(self._abort)
        self.stack.moveToThread(self.worker)

        # Status bar
        # ==================================================
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.setGeometry(30, 40, 200, 25)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.setup_statusbar()

        # Slots & signals
        # ==================================================
        self.stack.update_progress.connect(self._update_progress_bar)
        self.dock.sig_show_inactive_plots.connect(self.splitview._show_inactive_plots)
        self.dock.sig_set_active_plot_colour.connect(
            self.splitview._set_active_plot_colour
        )
        self.dock.sig_set_inactive_plot_colour.connect(
            self.splitview._set_inactive_plot_colour
        )
        self.dock.sig_set_slice_contour_colour.connect(
            self.canvas._set_slice_contour_colour
        )
        self.dock.sig_set_radial_segments.connect(self.stack._slot_compute_radial_profile)
        self.dock.sig_set_phase_segments.connect(self.stack._slot_compute_phase_profile)

        # Load the tab
        # ==================================================
        self._load_tab()

    def setup_statusbar(self):

        pass

    def _update_progress_bar(self, path: Path):
        self.status_bar.showMessage(f"Processing {path}")
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def setup_toolbar(self):

        # Dock widget toggle
        act_dock = QAction(
            QIcon.fromTheme("document-properties"), "Show docking panel", self.toolbar
        )
        act_dock.triggered.connect(self._toggle_dock)
        self.toolbar.addAction(act_dock)

        # Scale image button
        act_scale_image = QAction(
            QIcon.fromTheme("zoom-fit-best"), "Scale image to fit", self.toolbar
        )
        act_scale_image.triggered.connect(self.canvas._reset_zoom)
        self.toolbar.addAction(act_scale_image)

        # # Find centre
        # act_find_centre = QAction(QIcon.fromTheme("tools-media-optical-format"), "Reset centre", self.toolbar)
        # act_find_centre.triggered.connect(lambda: self.canvas._reset_centre())
        # self.toolbar.addAction(act_find_centre)

        # # Radial profile button
        # act_radial_profile = QAction(QIcon.fromTheme("object-rotate-left"), "Plot radial profile", self.toolbar)
        # act_radial_profile.triggered.connect(self.canvas.layer.compute_radial_profile)
        # self.toolbar.addAction(act_radial_profile)

        # # Radial plot button
        # act_plot = QAction(QIcon.fromTheme("list-add"), "Plot radial profile", self.toolbar)
        # act_plot.triggered.connect(lambda: self.splitview.plot(self.stack.current_layer))
        # self.toolbar.addAction(act_plot)

    @Slot()
    def _toggle_dock(self):
        if self.dock.isVisible():
            self.dock.hide()
        else:
            self.dock.show()

    @Slot()
    def _set_threshold(
        self,
        update: bool = True,
    ):
        self.dock._slot_show_inactive_plots()
        self.stack._update_threshold(self.dock.show_inactive_plots)

    def _load_tab(self):
        self.status_bar.showMessage(f"Loading stack from {self.paths[0].parent}...")
        self.progress_bar.show()
        self.load_stack.emit()

    def _abort(self):
        self.worker.quit()

    @Slot()
    def set_canvas(self):

        self.status_bar.showMessage(f"Setting up canvas...")
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.worker.quit()
        self.canvas.set_stack(self.stack, auto_range=True)
        self.status_bar.clearMessage()
        self.setup_toolbar()
