import pyqtgraph as pg


class Target(pg.TargetItem):
    def __init__(
        self,
        pos: tuple,
        *args,
        **kwargs,
    ):

        kwargs.setdefault("movable", False)
        super().__init__(pos, *args, **kwargs)
