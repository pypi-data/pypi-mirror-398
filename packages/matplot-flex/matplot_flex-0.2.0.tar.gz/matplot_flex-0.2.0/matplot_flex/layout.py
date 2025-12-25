from dataclasses import dataclass
from typing import Literal, Optional

import matplotlib.pyplot as plt

from .axes_utils import get_primary_axes

# デバッグ用に枠を表示する場合は True にする
IS_VISIBLE_FRAME = False


@dataclass(frozen=True)
class GraphModule:
    x_axis: plt.Figure
    x_label: plt.Figure
    y_label: plt.Figure
    y_axis: plt.Figure
    main: plt.Figure
    title: plt.Figure


def draw_debug_frame(figs) -> None:
    for f in figs:
        ax = get_primary_axes(f)
        ax.set_axis_on()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor("none")
        for spine in ax.spines.values():
            spine.set_visible(True)


def get_pixel_size(fig) -> tuple[int, int]:
    """
    Figure または SubFigure の現在の幅と高さをピクセル単位で返す。
    """
    fig.canvas.draw()
    bbox = fig.bbox
    return bbox.width, bbox.height


def create_fig(width: int = 1280, height: int = 720) -> plt.Figure:
    return plt.figure(figsize=(width / 100, height / 100), dpi=100)


def divide_fig_ratio(fig, direction: Literal["horizontal", "vertical"], ratios: list[float]) -> list[plt.Figure]:
    n_areas = len(ratios)
    if direction == "horizontal":
        figs = fig.subfigures(1, n_areas, width_ratios=ratios, wspace=0, hspace=0)
    else:
        figs = fig.subfigures(n_areas, 1, height_ratios=ratios, wspace=0, hspace=0)
    if IS_VISIBLE_FRAME:
        draw_debug_frame(figs)
    return figs


def divide_fig_pixel(fig, direction: Literal["horizontal", "vertical"], sizes: list[Optional[float]]) -> list[plt.Figure]:
    """
    sizes に None が含まれる場合は残余を均等割り当てし、全指定が親を超える場合は例外を投げる。
    """
    parent_width, parent_height = get_pixel_size(fig)
    total_size = parent_width if direction == "horizontal" else parent_height

    n_areas = len(sizes)
    specified_total = sum([s for s in sizes if s is not None])
    if specified_total > total_size:
        raise ValueError("The specified sizes exceed the parent figure size.")
    n_none = sizes.count(None)
    if n_none > 0:
        remaining_size = total_size - specified_total
        size_per_none = remaining_size / n_none
        sizes = [s if s is not None else size_per_none for s in sizes]
    ratios = [s / total_size for s in sizes]

    if direction == "horizontal":
        figs = fig.subfigures(1, n_areas, width_ratios=ratios, wspace=0, hspace=0)
    else:
        figs = fig.subfigures(n_areas, 1, height_ratios=ratios, wspace=0, hspace=0)

    if IS_VISIBLE_FRAME:
        draw_debug_frame(figs)
    return figs


def get_padding_subfig(fig, padding: float = 0.1) -> plt.Figure:
    """
    親Figureの中に、指定されたpadding(割合)を空けた新しいSubFigureを作成して返す。
    GridSpecの比率(ratios)を使うことで、constrained_layout環境下でもパディングを死守する。
    """
    gs = fig.add_gridspec(
        3,
        3,
        width_ratios=[padding, 1.0 - 2 * padding, padding],
        height_ratios=[padding, 1.0 - 2 * padding, padding],
        wspace=0,
        hspace=0,
    )

    subfig = fig.add_subfigure(gs[1, 1])
    subfig.set_facecolor("none")
    if IS_VISIBLE_FRAME:
        draw_debug_frame([subfig])
    return subfig


def draw_graph_module(fig, title_ratio=0.2, label_ratio=0.1, axis_ratio=0.05) -> GraphModule:
    parent_width, parent_height = get_pixel_size(fig)
    title_width = int(min(parent_width, parent_height) * title_ratio)
    label_width = int(min(parent_width, parent_height) * label_ratio)
    axis_width = int(min(parent_width, parent_height) * axis_ratio)
    upper, lower = divide_fig_pixel(fig, "vertical", sizes=[None, axis_width + label_width + title_width])
    _, lower, _ = divide_fig_pixel(lower, "horizontal", sizes=[axis_width + label_width, None, axis_width + label_width])
    horizontal_axis, horizontal_label, title = divide_fig_pixel(lower, "vertical", sizes=[axis_width, label_width, title_width])
    vertical_label, vertical_axis, main, _ = divide_fig_pixel(upper, "horizontal", sizes=[label_width, axis_width, None, axis_width + label_width])
    return GraphModule(
        x_axis=horizontal_axis,
        x_label=horizontal_label,
        y_label=vertical_label,
        y_axis=vertical_axis,
        main=main,
        title=title,
    )


__all__ = [
    "IS_VISIBLE_FRAME",
    "GraphModule",
    "create_fig",
    "divide_fig_ratio",
    "divide_fig_pixel",
    "get_padding_subfig",
    "draw_graph_module",
]
