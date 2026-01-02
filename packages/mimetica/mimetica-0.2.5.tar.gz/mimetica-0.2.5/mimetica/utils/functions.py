import skimage as ski
import shapely as shp
from shapely.geometry import Polygon
import numpy as np
from PySide6.QtGui import QColor
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QColorDialog


def compute_minimal_bounding_circle(image: np.ndarray):
    '''
    Compute the minimal bounding circle (MBC) and radius.

    Args:
        image: The image being analysed.

    Returns:
        The MBC and its radius.
    '''

    point_set = np.argwhere(image)
    points = shp.MultiPoint(point_set)

    mbc = shp.minimum_bounding_circle(points)
    mbr = shp.minimum_bounding_radius(points)
    return mbc, mbr


def draw_sorted_circle(centre: np.ndarray, radius: np.ndarray):
    rr, cc = ski.draw.circle_perimeter(
        *centre.astype(np.uint32),
        np.floor(radius).astype(np.uint32),
        method="andres",
    )
    rr = np.array(rr, dtype=np.uint32)
    cc = np.array(cc, dtype=np.uint32)
    angle = np.argsort(np.arctan2(cc - np.mean(cc), rr - np.mean(rr)))
    rr = np.take(rr, angle, axis=0)
    cc = np.take(cc, angle, axis=0)
    return rr, cc


def as_rgba(colour: QColor) -> str:
    """
    Convert a QColor isntance (including opacity) into RGBA format
    suitable for use in a stylesheet.

    The R, G and B values are between 0 and 255, and the opacity
    is between 0 and 1.

    Args:
        colour:
            A QColor instance.

    Returns:
        RGBA-formatted string.
    """
    return ",".join(
        str(c)
        for c in [
            colour.red(),
            colour.green(),
            colour.blue(),
            colour.alphaF(),
        ]
    )


def as_hex(colour: QColor) -> str:
    """
    Convert a QColor isntance (including opacity) into hex format.

    Args:
        colour:
            A QColor instance.

    Returns:
        The hex representation.
    """
    return "#" + "".join(
        [
            f"{colour.red():02X}",
            f"{colour.green():02X}",
            f"{colour.blue():02X}",
            f"{colour.alpha():02X}",
        ]
    )


def get_colour(
    initial: QColor = None,
    parent: QObject = None,
    title: str = "Pick a colour",
) -> QColor:
    """
    Get a QColor from a QColorDialog.

    Returns:
        The selected colour.
    """

    return QColorDialog.getColor(
        initial,
        parent,
        title,
        QColorDialog.ColorDialogOption.ShowAlphaChannel,
    )
