from dataclasses import dataclass
from datetime import datetime
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor
from omegaconf import OmegaConf

@dataclass
class Conf(QSettings):
    WindowGeometry: str = "window/geometry"
    WindowPosition: str = "window/position"
    InactivePlotColour: str = "plots/inactive/colour"
    ShowInactivePlots: str = "plots/inactive/show"
    ActivePlotColour: str = "plots/active/colour"
    InactiveSliceColour: str = "slice/inactive/colour"
    ActiveSliceColour: str = "slice/active/colour"
    SliceContourColour: str = "slice/contour/colour"
    ShowStack: bool = "stack/show"
    RadialSamples: int = "analysis/radial_samples"
    PhaseSamples: int = "analysis/phase_samples"

    def __init__(self, *args, **kwargs):
        super().__init__("Mimetica", "Mimetica", *args, **kwargs)
        self.setValue("Copyright", f"{datetime.now().year} Alexander Hadjiivanov")

    @property
    def window_geometry(self):
        pass

    # Show inactive plots
    @property
    def show_inactive_plots(self) -> bool:
        return self.value(Conf.ShowInactivePlots, True, bool)

    @show_inactive_plots.setter
    def show_inactive_plots(
        self,
        value: QColor,
    ):
        self.setValue(Conf.ShowInactivePlots, value)

    # Inactive plot colour
    @property
    def inactive_plot_colour(self) -> QColor:
        return self.value(
            Conf.InactivePlotColour,
            QColor(147, 147, 147, 100),
            QColor,
        )

    @inactive_plot_colour.setter
    def inactive_plot_colour(
        self,
        value: QColor,
    ):
        self.setValue(Conf.InactivePlotColour, value)

    # Active plot colour
    @property
    def active_plot_colour(self) -> QColor:
        return self.value(
            Conf.ActivePlotColour,
            QColor(51, 255, 51, 255),
            QColor,
        )

    @active_plot_colour.setter
    def active_plot_colour(
        self,
        value: QColor,
    ):
        self.setValue(Conf.ActivePlotColour, value)

    # Slice contour colour
    @property
    def slice_contour_colour(self) -> QColor:
        return self.value(
            Conf.SliceContourColour,
            QColor(255, 255, 0, 255),
            QColor,
        )

    @slice_contour_colour.setter
    def slice_contour_colour(
        self,
        value: QColor,
    ):
        self.setValue(Conf.SliceContourColour, value)

    # Show stack
    @property
    def show_stack(self) -> bool:
        return self.value(Conf.ShowStack, True, bool)

    @show_stack.setter
    def show_stack(
        self,
        value: bool,
    ):
        self.setValue(Conf.ShowStack, value)

    # Radial segments
    @property
    def radial_samples(self) -> int:
        return self.value(Conf.RadialSamples, 200, int)

    @radial_samples.setter
    def radial_samples(
        self,
        value: int,
    ):
        self.setValue(Conf.RadialSamples, value)

    # Phase segments
    @property
    def phase_samples(self) -> int:
        return self.value(Conf.PhaseSamples, 360, int)

    @phase_samples.setter
    def phase_samples(
        self,
        value: int,
    ):
        self.setValue(Conf.PhaseSamples, value)


conf = Conf()
