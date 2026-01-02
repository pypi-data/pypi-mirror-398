import pyqtgraph as pg


class Contour(pg.CircleROI):
    """
    Circular contour subclass.
    """

    def __init__(self, pos, radius, **args):

        args.setdefault("movable", False)
        args.setdefault("resizable", False)
        args.setdefault("removable", False)
        args.setdefault("rotatable", False)

        pg.CircleROI.__init__(
            self,
            pos,
            1,
            **args,
        )

        for h in self.getHandles():
            self.removeHandle(h)

        self.setSize(2 * radius, (0.5, 0.5), update=True, finish=True)
