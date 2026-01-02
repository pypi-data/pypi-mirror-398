from pathlib import Path

import numpy as np

import shapely as shp

from concurrent.futures import ProcessPoolExecutor

from PySide6.QtCore import Slot
from PySide6.QtCore import Signal
from PySide6.QtCore import QObject

from mimetica import Layer
from mimetica import utils
from mimetica import logger


class Stack(QObject):
    update_progress = Signal(Path)
    set_canvas = Signal()
    abort = Signal()

    @staticmethod
    def make_layer(
        path: str | Path,
    ):
        """
        Create a layer for the given image.

        Args:
            path: Path to the image file.

        Returns:
            A layer instance.
        """
        return Layer(path)

    def __init__(
        self,
        paths: list[Path],
        threshold: int = 70,
        *args,
        **kwargs,
    ):
        """
        Create a stack of images.

        Args:
            paths: A list of image paths.
            threshold: Binarisation threshold (only for RGB or greyscale images; currently unused)
        """
        super().__init__(*args, **kwargs)

        # Save the parameters
        # ==================================================
        self.paths = sorted(paths)
        self.threshold = threshold

        # Other attributes
        # ==================================================
        self.layers = []
        self.active_layer = 0

        # Create a merged stack
        # ==================================================
        self.merged: np.ndarray = None

    def _set_active_layer(
        self,
        index: int = 0,
    ):
        """
        Set the layer to the given index.

        Args:
            index: Layer index.
        """
        self.active_layer = index

    @Slot(int)
    def _slot_compute_radial_profile(
        self,
        segments: int,
    ):
        '''
        Update the radial profile with a new number of segments.

        Args:
            segments: Number of radial segments.
        '''

        for layer in self.layers:
            layer.compute_radial_profile()
        self.plot.emit()

    @Slot(int)
    def _slot_compute_phase_profile(
        self,
        segments: int,
    ):
        '''
        Update the phase profile with a new number of segments.

        Args:
            segments: Number of phase segments.
        '''
        for layer in self.layers:
            layer.compute_phase_profile()

        self.plot.emit()

    @Slot()
    def process(self):
        """
        Process a stack of images.
        """
        logger.info(f"Loading stack...")

        # Layer factory
        # ==================================================
        with ProcessPoolExecutor() as executor:
            for layer in executor.map(Stack.make_layer, self.paths):
                self.layers.append(layer)
                self.update_progress.emit(layer.path)

        self._set_active_layer()

        # Calibrate the stack based on all the images
        # ==================================================
        for layer in self.layers:

            if self.merged is None:
                self.merged = layer.image.copy().astype(np.float32)
            else:
                self.merged += layer.image

        # Scale the merged stack
        # ==================================================
        minval = self.merged.min()
        maxval = self.merged.max()
        self.merged = (255 * (self.merged - minval) / (maxval - minval)).astype(
            np.uint8
        )

        # Set the stack on the canvas
        # ==================================================
        self.set_canvas.emit()
