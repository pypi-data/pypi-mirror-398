from PySide6.QtCore import Qt
from PySide6.QtCore import Slot
from PySide6.QtCore import Signal
from PySide6.QtCore import QEvent
from PySide6.QtCore import QObject

from PySide6.QtGui import QKeyEvent
from PySide6.QtGui import QMouseEvent
from PySide6.QtGui import QEnterEvent

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QScrollArea
from PySide6.QtWidgets import QSizePolicy

import numpy as np
import skimage as ski

import pyqtgraph as pg
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
from pyqtgraph import SignalProxy

from mimetica import Thumbnail
from mimetica import ImageView
from mimetica import Layer
from mimetica import Stack
from mimetica import conf
from mimetica.gui.display.roi.contour import Contour
from mimetica.gui.display.roi.target import Target


class Canvas(QWidget):
    plot = Signal()
    highlight_plot = Signal(int)
    update_radial_plot = Signal(float)
    update_phase_plot = Signal(float)

    class EventHandler(QObject):

        ctrl_signal = Signal(bool)
        focus_signal = Signal()

        def __init__(self, wh, *args, **kwargs):

            super().__init__(*args, **kwargs)
            self.wh = wh

        def eventFilter(self, obj: QObject, event: QEvent):
            if obj is self.wh:
                if isinstance(event, QEnterEvent):
                    self.focus_signal.emit()
                elif isinstance(event, QKeyEvent) and event.key() == Qt.Key.Key_Control:
                    if event.type() == QKeyEvent.Type.KeyPress:
                        self.ctrl_signal.emit(True)
                    elif event.type() == QKeyEvent.Type.KeyRelease:
                        self.ctrl_signal.emit(False)
            return QObject().eventFilter(obj, event)

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # Image viewport
        # ==================================================
        self.iv = ImageView(self)

        # Current stack
        # ==================================================
        self.stack = None

        # Arrays used for displaying parts of the layer
        # ==================================================
        self.image = None
        self.centre = None
        self.stack_mbc = None
        self.layer_mbcs = []
        self.phase_resolution = 1

        # Layout grid
        # ==================================================
        self.grid = QGridLayout(self)
        self.grid.addWidget(self.iv, 0, 0, 1, 2)

        # Thumbnails
        # ==================================================
        self.thumbnails = []
        self.tb_widget = QWidget()
        self.tb_scroll_area = QScrollArea(self)
        self.tb_layout = QHBoxLayout()
        self.tb_layout.setContentsMargins(0, 0, 0, 0)
        self.tb_widget.setLayout(self.tb_layout)

        # Layer highlighters
        # ==================================================
        self.slice_contour_pen = pg.mkPen(color=conf.slice_contour_colour, width=1)
        self.slice_contour = None
        self.slice_centre_pen = pg.mkPen(
            color=conf.slice_contour_colour, width=1
        )  # TODO: Separate conf entry
        self.slice_centre = None

        # Stack highlighters
        # ==================================================
        self.stack_contour_pen = pg.mkPen(color=conf.stack_contour_colour, width=1)
        self.stack_contour = None

        self.tb_scroll_area.setFixedHeight(110)
        self.tb_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.tb_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.tb_scroll_area.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self.tb_scroll_area.setWidgetResizable(True)
        self.tb_scroll_area.setWidget(self.tb_widget)

        self.grid.addWidget(self.tb_scroll_area, 1, 0, 1, 2)

        # Slots, signals and proxies
        # ==================================================

        # Mouse tracking for the ROI
        # ==================================================
        self.mouse_tracking_toggle = False
        self.mouse_tracker = SignalProxy(
            self.iv.scene.sigMouseMoved,
            rateLimit=100,
            slot=self._mouse_coordinates,
        )

        self.event_handler = Canvas.EventHandler(self)
        self.installEventFilter(self.event_handler)
        self.event_handler.ctrl_signal.connect(self._toggle_mouse_tracking)
        self.event_handler.focus_signal.connect(self._focus_canvas)

    @property
    def layer(self) -> Layer:
        return self.stack.layers[self.stack.current_layer]

    def set_stack(
        self,
        stack: Stack,
        auto_range: bool = False,
    ):
        # Update the stack
        # ==================================================
        self.stack = stack
        if len(self.stack.layers) > 0:
            self.stack._update_current_layer()

        # Update the thumbnails
        # ==================================================
        self._update_thumbnails()

        # Select the first layer
        # ==================================================
        self.slot_select_layer(0, auto_range)

    def process(
        self,
        auto_range: bool = False,
    ):
        # Paint the result onto the canvas
        # ==================================================
        self._draw(auto_range)

        # Set up the ROI
        # ==================================================
        self.iv.set_roi(self.layer)

        # Plot the radial and phase profiles
        # ==================================================
        self.plot.emit()

    def _draw(
        self,
        auto_range: bool = False,
    ):
        # Coordinates of the current layer and the stack
        # ==================================================
        lcx, lcy = self.layer.centre
        scx, scy = self.stack.centre

        # # Reset the canvas
        # # ==================================================
        self.image = np.zeros(self.stack.merged.shape + (4,))

        # Draw the slice and potentially the stack
        # ==================================================
        # if conf.show_stack:
        #     idx = np.argwhere(self.stack.merged > 0).T
        #     self.image[idx[0], idx[1], 0] = conf.stack_contour_colour.red()
        #     self.image[idx[0], idx[1], 1] = conf.stack_contour_colour.green()
        #     self.image[idx[0], idx[1], 2] = conf.stack_contour_colour.blue()
        #     self.image[idx[0], idx[1], 3] = conf.stack_contour_colour.alpha()

        idx = np.argwhere(self.layer.image > 0).T
        self.image[idx[0], idx[1], :3] = ski.exposure.rescale_intensity(
            self.layer.image[idx[0], idx[1], None],
            in_range=np.ubyte,
            out_range=(0.0, 1.0),
        ) * np.array(
            [
                conf.slice_contour_colour.red(),
                conf.slice_contour_colour.green(),
                conf.slice_contour_colour.blue(),
            ]
        )
        # self.image[..., :3] = ski.exposure.rescale_intensity(
        #     self.layer.image[:,:,None],
        #     in_range=np.ubyte,
        #     out_range=(0.0, 1.0),
        # ) * np.array(
        #     [
        #         conf.slice_contour_colour.red(),
        #         conf.slice_contour_colour.green(),
        #         conf.slice_contour_colour.blue(),
        #     ]
        # )
        # self.image[idx[0], idx[1], 1] = self.layer.image[..., 1] # * conf.slice_contour_colour.green()
        # self.image[idx[0], idx[1], 2] = self.layer.image[..., 2] # * conf.slice_contour_colour.blue()
        self.image[idx[0], idx[1], 3] = conf.slice_contour_colour.alpha()

        # Draw the centre
        # ==================================================
        if self.slice_centre is not None:
            self.iv.removeItem(self.slice_centre)
        self.slice_centre = Target(
            (lcy + 0.5, lcx + 0.5),
            pen=self.slice_centre_pen,
        )
        self.iv.addItem(self.slice_centre)

        # Draw the slice contour
        # ==================================================
        if self.slice_contour is not None:
            self.iv.removeItem(self.slice_contour)
        self.slice_contour = Contour(
            (lcy + 0.5, lcx + 0.5),
            radius=self.layer.mbr,
            pen=self.slice_contour_pen,
        )
        self.iv.addItem(self.slice_contour)

        # Draw the stack contour
        # ==================================================
        if self.stack_contour is not None:
            self.iv.removeItem(self.stack_contour)
        self.stack_contour = Contour(
            (scy + 0.5, scx + 0.5),
            radius=self.stack.radius,
            pen=self.stack_contour_pen,
        )
        self.iv.addItem(self.stack_contour)

        # Set the image
        # ==================================================
        self.iv.setImage(
            self.image, autoRange=auto_range, levels=(0, 255), levelMode="rgba"
        )

    def _update_thumbnails(self):
        while True:
            item = self.tb_layout.takeAt(0)
            if item is None or item.isEmpty():
                break
            self.tb_layout.removeWidget(item.widget())
            item.widget().deleteLater()

        self.thumbnails.clear()
        for index, layer in enumerate(self.stack.layers):
            tb = Thumbnail(index, layer, self, 90)
            tb._selected.connect(self.slot_select_layer)
            self.thumbnails.append(tb)

        for idx, tb in enumerate(self.thumbnails):
            self.tb_layout.addWidget(tb, alignment=Qt.AlignmentFlag.AlignLeft)

        self.tb_layout.addStretch()

    @Slot()
    def _reset_zoom(self):
        self._draw(auto_range=True)

    def eventFilter(self, obj, event):
        if obj is self.window:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Control:
                    self.ctrl_signal.emit(True)
            if event.type() == QEvent.KeyRelease:
                if event.key() == Qt.Key_Control:
                    self.ctrl_signal.emit(False)
        return super().eventFilter(obj, event)

    @Slot()
    def _mouse_coordinates(
        self,
        event: MouseClickEvent,
    ):

        if self.mouse_tracking_toggle:
            if self.iv.radial_roi is not None:
                pos = self.iv.getView().vb.mapSceneToView(event)[0]

                cx = pos.x() - self.layer.centre[1] - 0.5
                cy = pos.y() - self.layer.centre[0] - 0.5
                r = np.sqrt(cx**2 + cy**2)
                radius = r / self.layer.mbr
                r2 = 2 * r
                if radius <= 1:
                    phase = 0 if r == 0 else np.rad2deg(np.arccos(cx / r))

                    if cy < 0:
                        phase = 360 - phase

                    self.iv.radial_roi.setSize(
                        r2,
                        center=(0.5, 0.5),
                        update=True,
                        finish=True,
                    )
                    self.iv.phase_roi.set_end(pos)
                    self.update_radial_plot.emit(radius)
                    self.update_phase_plot.emit(phase)

    @Slot(bool)
    def _toggle_mouse_tracking(
        self,
        toggle: bool,
    ):
        self.mouse_tracking_toggle = toggle
        # self.iv.phase_roi.setVisible(toggle)
        # self.iv.radial_roi.setVisible(toggle)

    @Slot()
    def _focus_canvas(self):
        self.setFocus()

    @Slot()
    def _set_slice_contour_colour(self):
        self.slice_contour_pen = pg.mkPen(color=conf.slice_contour_colour, width=1)
        self._draw()

    @Slot()
    def _set_stack_contour_colour(self):
        self.stack_contour_pen = pg.mkPen(color=conf.stack_contour_colour, width=1)
        self._draw()

    @Slot()
    def _set_show_stack(self):
        self._draw()

    @Slot(int)
    def _slot_compute_radial_profile(self, segments: int):
        if self.layer is None:
            return

        self.layer.compute_radial_profile()
        self.plot.emit()

    @Slot(int)
    def _slot_compute_phase_profile(self, segments: int):
        if self.layer is None:
            return

        self.layer.compute_phase_profile()
        self.plot.emit()

    @Slot(int, bool)
    def slot_select_layer(
        self,
        layer: int,
        auto_range: bool = False,
    ):
        cur_layer = self.stack.current_layer
        if cur_layer is None:
            cur_layer = 0

        # Update the layer
        self.stack._update_current_layer(layer)

        # Highlight the selected thumbnail
        self.thumbnails[cur_layer].deselect()
        self.thumbnails[layer].select()

        # Process the layer
        self.process(auto_range)

        # Emit a signal to highlight the relevant plots
        self.highlight_plot.emit(layer)
