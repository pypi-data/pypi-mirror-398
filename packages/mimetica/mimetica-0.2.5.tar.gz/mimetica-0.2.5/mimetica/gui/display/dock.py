from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QDockWidget
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QFormLayout
from PySide6.QtWidgets import QSizePolicy

from mimetica import conf
from mimetica.utils.functions import as_rgba
from mimetica.utils.functions import get_colour


class Dock(QDockWidget):
    sig_show_inactive_plots = Signal()
    sig_set_active_plot_colour = Signal()
    sig_set_inactive_plot_colour = Signal()
    sig_set_stack_contour_colour = Signal()
    sig_set_slice_contour_colour = Signal()
    sig_show_stack = Signal()
    sig_set_radial_segments = Signal(int)
    sig_set_phase_segments = Signal(int)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        title = QLabel("Settings", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 14pt; font-weight: bold; text-align: center;")
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setTitleBarWidget(title)

        self.setVisible(False)
        self.setMinimumWidth(200)
        topright = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight

        self.grid = QFormLayout()

        # Show all plots checkbox
        # ==================================================
        self.show_inactive_plots_lbl = QLabel(f"Show all plots:", self)
        self.show_inactive_plots_cbox = QCheckBox(self)
        self.show_inactive_plots_cbox.setChecked(conf.show_inactive_plots)
        self.grid.addRow(self.show_inactive_plots_lbl, self.show_inactive_plots_cbox)
        self.show_inactive_plots_cbox.stateChanged.connect(
            self._slot_show_inactive_plots
        )

        # Active plot colour
        # ==================================================
        self.active_plot_colour_lbl = QLabel(f"Active plot colour:", self)
        self.active_plot_colour_btn = QPushButton(self)
        self.active_plot_colour_btn.setStyleSheet(
            f"background-color:rgba({as_rgba(conf.active_plot_colour)});"
        )
        self.grid.addRow(self.active_plot_colour_lbl, self.active_plot_colour_btn)
        self.active_plot_colour_btn.pressed.connect(self._slot_set_active_plot_colour)

        # Inactive plot colour
        # ==================================================
        self.inactive_plot_colour_lbl = QLabel(f"Inactive plot colour:", self)
        self.inactive_plot_colour_btn = QPushButton(self)
        self.inactive_plot_colour_btn.setStyleSheet(
            f"background-color:rgba({as_rgba(conf.inactive_plot_colour)});"
        )
        self.grid.addRow(self.inactive_plot_colour_lbl, self.inactive_plot_colour_btn)
        self.inactive_plot_colour_btn.pressed.connect(
            self._slot_set_inactive_plot_colour
        )

        # Stack contour colour
        # ==================================================
        self.stack_contour_colour_lbl = QLabel(f"Stack contour colour:", self)
        self.stack_contour_colour_btn = QPushButton(self)
        self.stack_contour_colour_btn.setStyleSheet(
            f"background-color:rgba({as_rgba(conf.stack_contour_colour)});"
        )
        self.grid.addRow(self.stack_contour_colour_lbl, self.stack_contour_colour_btn)
        self.stack_contour_colour_btn.pressed.connect(
            self._slot_set_stack_contour_colour
        )

        # Slice contour colour
        # ==================================================
        self.slice_contour_colour_lbl = QLabel(f"Slice contour colour:", self)
        self.slice_contour_colour_btn = QPushButton(self)
        self.slice_contour_colour_btn.setStyleSheet(
            f"background-color:rgba({as_rgba(conf.slice_contour_colour)});"
        )
        self.grid.addRow(self.slice_contour_colour_lbl, self.slice_contour_colour_btn)
        self.slice_contour_colour_btn.pressed.connect(
            self._slot_set_slice_contour_colour
        )

        # Show the stack
        # ==================================================
        self.show_stack_lbl = QLabel(f"Show the stack:", self)
        self.show_stack_cbox = QCheckBox(self)
        self.show_stack_cbox.setChecked(conf.show_stack)
        self.grid.addRow(self.show_stack_lbl, self.show_stack_cbox)
        self.show_stack_cbox.stateChanged.connect(self._slot_show_stack)

        # Radial segments
        # ==================================================
        self.radial_segments_lbl = QLabel(f"Radial segments:", self)
        self.radial_segments_sbox = QSpinBox(
            self,
            value=conf.radial_segments,
            minimum=1,
            maximum=1024,
            singleStep=1,
        )
        self.radial_segments_sbox.setValue(conf.radial_segments)
        self.grid.addRow(self.radial_segments_lbl, self.radial_segments_sbox)
        self.radial_segments_sbox.valueChanged.connect(self._slot_set_radial_segments)

        # Phase segments
        # ==================================================
        self.phase_segments_lbl = QLabel(f"Phase segments:", self)
        self.phase_segments_sbox = QSpinBox(
            self,
            value=conf.phase_segments,
            minimum=120,
            maximum=720,
            singleStep=1,
            suffix="°",
        )
        self.phase_segments_sbox.setValue(conf.phase_segments)
        self.grid.addRow(self.phase_segments_lbl, self.phase_segments_sbox)
        self.phase_segments_sbox.valueChanged.connect(self._slot_set_phase_segments)

        # Set up the main widget
        # ==================================================
        self.body = QWidget()
        self.setWidget(self.body)
        self.body.setLayout(self.grid)
        self.body.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    @Slot()
    def _slot_show_inactive_plots(self):
        conf.show_inactive_plots = self.show_inactive_plots_cbox.isChecked()
        self.sig_show_inactive_plots.emit()

    @Slot()
    def _slot_set_active_plot_colour(self):
        colour = get_colour(conf.active_plot_colour, self)
        if colour.isValid():
            conf.active_plot_colour = colour
            self.sig_set_active_plot_colour.emit()
            self.active_plot_colour_btn.setStyleSheet(
                f"background-color:rgba({as_rgba(colour)});"
            )

    @Slot()
    def _slot_set_inactive_plot_colour(self):
        colour = get_colour(conf.inactive_plot_colour, self)
        if colour.isValid():
            conf.inactive_plot_colour = colour
            self.sig_set_inactive_plot_colour.emit()
            self.inactive_plot_colour_btn.setStyleSheet(
                f"background-color:rgba({as_rgba(colour)});"
            )

    @Slot()
    def _slot_set_stack_contour_colour(self):
        colour = get_colour(conf.stack_contour_colour, self)
        if colour.isValid():
            conf.stack_contour_colour = colour
            self.sig_set_stack_contour_colour.emit()
            self.stack_contour_colour_btn.setStyleSheet(
                f"background-color:rgba({as_rgba(colour)});"
            )

    @Slot()
    def _slot_set_slice_contour_colour(self):
        colour = get_colour(conf.slice_contour_colour, self)
        if colour.isValid():
            conf.slice_contour_colour = colour
            self.sig_set_slice_contour_colour.emit()
            self.slice_contour_colour_btn.setStyleSheet(
                f"background-color:rgba({as_rgba(colour)});"
            )

    @Slot()
    def _slot_show_stack(self):
        conf.show_stack = self.show_stack_cbox.isChecked()
        self.sig_show_stack.emit()

    @Slot()
    def _slot_set_radial_segments(self):
        conf.radial_segments = self.radial_segments_sbox.value()
        self.sig_set_radial_segments.emit(conf.radial_segments)

    @Slot()
    def _slot_set_phase_segments(self):
        conf.phase_segments = self.phase_segments_sbox.value()
        self.sig_set_phase_segments.emit(conf.phase_segments)

