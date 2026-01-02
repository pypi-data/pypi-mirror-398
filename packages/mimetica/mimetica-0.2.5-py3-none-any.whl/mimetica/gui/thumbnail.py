from PySide6.QtCore import QEvent
from PySide6.QtCore import Signal

from PySide6.QtGui import QPixmap
from PySide6.QtGui import QImage

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QLabel

from mimetica import Layer


class Thumbnail(QLabel):

    _selected = Signal(int)

    def __init__(
        self,
        index: int,
        layer: Layer,
        parent: QWidget = None,
        scale: int = 75,
        border_size: int = 2,
    ):
        super().__init__(parent)

        self.index = index
        self.layer = layer

        (height, width) = layer.image.shape
        self.border_size = border_size

        qimg = QImage(layer.path)
        pxm = QPixmap(qimg).scaledToHeight(scale - 2 * self.border_size)
        self.setPixmap(pxm)
        self.setFixedHeight(scale)
        self.setStyleSheet(f"border: {self.border_size}px solid #000000;")

    def mousePressEvent(
        self,
        event: QEvent,
    ):
        self._selected.emit(self.index)

    def deselect(self):
        self.setStyleSheet(f"border: {self.border_size}px solid #000000;")

    def select(self):
        self.setStyleSheet(f"border: {self.border_size}px solid #00aa11;")
