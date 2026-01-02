import pyqtgraph as pg

from mimetica import Layer
from mimetica.gui.display.roi.line import RadialLine
from mimetica.gui.display.roi.contour import Contour


class ImageView(pg.ImageView):
    def __init__(
        self,
        *args,
        **kwargs,
    ):

        plot = pg.PlotItem()
        plot.setLabel(axis="left", text="Y-axis")
        plot.setLabel(axis="bottom", text="X-axis")
        kwargs["view"] = plot
        super().__init__(*args, **kwargs)

        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()

        self.radial_roi = None
        self.phase_roi = None

        self.view.invertX(False)
        self.view.invertY(False)

    def set_roi(
        self,
        layer: Layer,
    ):
        (cx, cy) = layer.centre[0], layer.centre[1]

        if self.radial_roi is not None:
            self.removeItem(self.radial_roi)
        self.radial_roi = Contour((cy, cx), radius=1)
        self.addItem(self.radial_roi)

        if self.phase_roi is not None:
            self.removeItem(self.phase_roi)
        self.phase_roi = RadialLine([(cy + 0.5, cx + 0.5), (cy + 1, cx + 0.5)])
        self.addItem(self.phase_roi)
