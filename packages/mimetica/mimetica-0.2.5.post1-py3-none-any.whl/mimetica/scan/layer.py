from pathlib import Path

from PySide6.QtCore import Slot

import skimage as ski
import skimage.draw as skd

import shapely as shp

import numpy as np

from mimetica import conf
from mimetica import utils


class Layer:
    def __init__(
        self,
        path: Path,
    ):
        self.path = Path(path).resolve().absolute()
        self.image = np.fliplr(ski.io.imread(str(self.path), as_gray=True).T)
        h, w = self.image.shape

        # Image properties
        # ==================================================
        # Minimal bounding circle
        self.mbc, self.mbr = utils.compute_minimal_bounding_circle(self.image)
        mbc_x, mbc_y = self.mbc.boundary.coords.xy

        pad_lr = max(abs(min(0, min(mbc_x))), max(0, max(mbc_x) - w))
        pad_tb = max(abs(min(0, min(mbc_y))), max(0, max(mbc_y) - h))
        pad = int(max(pad_lr, pad_tb) + 1)

        # Pad the image to accommodate for the contour
        # ==================================================
        self.canvas = np.pad(
            self.image,
            pad,
            mode="constant",
            constant_values=0,
        )

        # Translate the minimal bounding circle to account for the padding
        self.mbc = shp.affinity.translate(self.mbc, pad, pad)
        self.centre = np.array(self.mbc.centroid.coords).flatten()
        self.radial_range = np.empty([])
        self.radial_profile = np.empty([])
        self.phase_range = np.empty([])
        self.phase_profile = np.empty([])
        self.intersections = []

        # Extract contour, centre, etc.
        # ==================================================
        self.process()

    def make_mask(self) -> np.ndarray:
        """
        Create a mask for this layer.

        Returns:
            A mask as a NumPy array.
        """
        Y, X = np.meshgrid[: self.canvas.shape[0], : self.canvas.shape[1]]
        mask = np.sqrt((X - self.centre[0]) ** 2 + (Y - self.centre[1]) ** 2)
        mask = np.exp(-3 * mask / mask.max())
        return mask

    def process(self):
        """
        Process this layer.
        For now, this is limited to computing the radial and phase profiles.
        """
        self.compute_radial_profile()
        self.compute_phase_profile()

    @Slot()
    def compute_radial_profile(self):
        # Create an empty array
        self.radial_profile = np.zeros((conf.radial_samples,))
        self.radial_range = np.linspace(0, 1, len(self.radial_profile))
        self.radii = np.linspace(1.0, self.mbr, conf.radial_samples)

        for idx, radius in enumerate(self.radii):
            # Create a virtual circle with the right radius.
            # The 'andres' method does not leave gaps between
            # consecutive rings if they are close enough.
            rr, cc = skd.circle_perimeter(
                int(self.centre[0]),
                int(self.centre[1]),
                int(radius),
                method="andres",
            )
            # Find out how much material is sampled by the circle
            # and compute the density
            circle = self.canvas[rr, cc]
            material = np.count_nonzero(circle)
            self.radial_profile[idx] = material / circle.size

    @Slot()
    def compute_phase_profile(self):
        # Coordinates of the central point
        (cx, cy) = self.centre

        # Compute the angles from the pixel coordinates.
        angles = conf.phase_samples

        # X and Y datasets for the phase profile
        self.phase_range = np.linspace(0, 360, angles, endpoint=False)
        self.phase_profile = np.zeros_like(self.phase_range)

        # Draw lines ('spokes') from the centre to the MBC, each rotated by
        # an angle determined by the number of phase samples.
        spokes = [
            shp.affinity.rotate(
                shp.LineString(
                    [
                        shp.Point(cx, cy),
                        shp.Point(cx, cy + self.mbr),
                    ],
                ),
                angle - 90,
                origin=shp.Point(cx, cy),
            )
            for angle in range(angles)
        ]

        for idx, spoke in enumerate(spokes):
            # (end_x, end_y) = self.intersections[idx]
            (cx, cy) = np.array(spoke.coords[0], dtype=np.int32)
            (ex, ey) = np.array(spoke.coords[1], dtype=np.int32)

            # Create a virtual line from the centre to the contour
            rr, cc = np.array(skd.line(cx, cy, ex, ey))

            # Find out how much material is sampled by the line
            # and compute the density
            line = self.canvas[rr, cc]
            material = np.count_nonzero(line)
            self.phase_profile[idx] = material / line.size
