from typing import Tuple

from matplotlib.axes import Axes


def _ensure_primary_axes(fig) -> Tuple[Axes, bool]:
    axes = fig.get_axes()
    if axes:
        return axes[0], False
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("none")
    return ax, True


def get_primary_axes(fig, *, hide_axis_on_create: bool = False) -> Axes:
    """
    Figure/SubFigureの主Axesを返す。存在しない場合は生成する。
    hide_axis_on_create=True の場合のみ、生成直後のAxesを axis off にする。
    """
    ax, created = _ensure_primary_axes(fig)
    if created and hide_axis_on_create:
        ax.set_axis_off()
    return ax


__all__ = ["get_primary_axes"]
