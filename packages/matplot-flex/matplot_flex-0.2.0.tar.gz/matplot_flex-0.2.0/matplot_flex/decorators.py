from typing import Any, Optional

import matplotlib.ticker as mticker
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from .config import AxisConfig, GridConfig, LegendConfig, LegendItem, LegendPosition
from .text_utils import draw_text


def apply_axis_limits(
    ax_main: Axes,
    x_cfg: AxisConfig,
    y_cfg: AxisConfig,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    ax_main.set_xlim(x_min, x_max)
    ax_main.set_ylim(y_min, y_max)
    ax_main.set_xscale(x_cfg.scale)
    ax_main.set_yscale(y_cfg.scale)
    ax_main.set_axis_on()


def draw_grid(
    ax_main: Axes,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    grid_cfg: GridConfig,
    x_locator: mticker.Locator,
    y_locator: mticker.Locator,
) -> None:
    if not grid_cfg.enabled:
        return
    gx_locator = grid_cfg.x_locator or x_locator
    gy_locator = grid_cfg.y_locator or y_locator
    x_ticks_grid = gx_locator.tick_values(x_min, x_max)
    y_ticks_grid = gy_locator.tick_values(y_min, y_max)

    for xt in x_ticks_grid:
        ax_main.axvline(
            xt,
            color=grid_cfg.color,
            linestyle=grid_cfg.linestyle,
            linewidth=grid_cfg.linewidth,
            zorder=0,
        )

    for yt in y_ticks_grid:
        ax_main.axhline(
            yt,
            color=grid_cfg.color,
            linestyle=grid_cfg.linestyle,
            linewidth=grid_cfg.linewidth,
            zorder=0,
        )


def draw_axis_tick_labels(
    ax_h_axis: Axes,
    ax_v_axis: Axes,
    x_cfg: AxisConfig,
    y_cfg: AxisConfig,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    x_locator: mticker.Locator,
    y_locator: mticker.Locator,
) -> None:
    ax_v_axis.set_ylim(y_min, y_max)
    y_ticks = y_locator.tick_values(y_min, y_max)
    for val in y_ticks:
        label_text = y_cfg.formatter(val) if y_cfg.formatter else f"{val:.1f}"
        draw_text(
            ax_v_axis,
            label_text,
            mode="fixed",
            fontsize=9,
            ha="right",
            va="center",
            x=0.90,
            y=val,
            transform=ax_v_axis.transData,
        )

    ax_h_axis.set_xlim(x_min, x_max)
    x_ticks = x_locator.tick_values(x_min, x_max)
    for val in x_ticks:
        label_text = x_cfg.formatter(val) if x_cfg.formatter else f"{val:.1f}"
        draw_text(
            ax_h_axis,
            label_text,
            mode="fixed",
            fontsize=9,
            ha="center",
            va="top",
            x=val,
            y=0.8,
            transform=ax_h_axis.transData,
        )


def draw_axis_labels(ax_h_label: Axes, ax_v_label: Axes, x_cfg: AxisConfig, y_cfg: AxisConfig) -> None:
    draw_text(ax_v_label, y_cfg.label, mode="fit", rotation=90, fontweight="bold", max_fontsize=20)
    draw_text(ax_h_label, x_cfg.label, mode="fit", fontweight="bold", max_fontsize=20)


def draw_title(ax_title: Axes, title: str) -> None:
    draw_text(ax_title, title, mode="fit", fontweight="bold", fontsize=16, max_fontsize=32)


def hide_main_ticks(ax_main: Axes) -> None:
    ax_main.set_xticks([])
    ax_main.set_yticks([])


def style_main_spines(ax_main: Axes, *, color: str = "black", linewidth: float = 1.0) -> None:
    for spine in ax_main.spines.values():
        spine.set_visible(True)
        spine.set_color(color)
        spine.set_linewidth(linewidth)


def _resolve_legend_position(position: LegendPosition, offset: tuple[float, float]) -> tuple[str, tuple[float, float]]:
    positions = {
        "upper center": ("upper center", (0.5, 1.0)),
        "upper left": ("upper left", (0.0, 1.0)),
        "upper right": ("upper right", (1.0, 1.0)),
        "lower center": ("lower center", (0.5, 0.0)),
        "lower left": ("lower left", (0.0, 0.0)),
        "lower right": ("lower right", (1.0, 0.0)),
        "center left": ("center left", (0.0, 0.5)),
        "center right": ("center right", (1.0, 0.5)),
        "center": ("center", (0.5, 0.5)),
    }
    if position not in positions:
        raise ValueError(f"Unknown legend position: {position}")
    loc, anchor = positions[position]
    return loc, (anchor[0] + offset[0], anchor[1] + offset[1])


def _resolve_legend_target(source_ax: Axes, legend: LegendConfig, target: Optional[Any]) -> Axes:
    target_obj = target if target is not None else legend.target
    if target_obj is None:
        return source_ax
    if isinstance(target_obj, Axes):
        return target_obj
    from .axes_utils import get_primary_axes

    return get_primary_axes(target_obj, hide_axis_on_create=True)


def _legend_handles(items: list[LegendItem]) -> tuple[list[Line2D], list[str]]:
    handles = []
    labels = []
    for item in items:
        handles.append(
            Line2D(
                [0],
                [0],
                color=item.color,
                linestyle=item.linestyle,
                marker=item.marker,
                linewidth=item.linewidth,
            )
        )
        labels.append(item.label)
    return handles, labels


def draw_legend(source_ax: Axes, legend: LegendConfig, *, target: Optional[Any] = None) -> None:
    if not legend.enabled or not legend.items:
        return
    target_ax = _resolve_legend_target(source_ax, legend, target)
    handles, labels = _legend_handles(legend.items)
    legend_kwargs = legend.to_kwargs()
    if legend.position is not None:
        loc, anchor = _resolve_legend_position(legend.position, legend.offset)
        legend_kwargs["loc"] = loc
        legend_kwargs["bbox_to_anchor"] = anchor
    target_ax.legend(handles, labels, **legend_kwargs)


__all__ = [
    "apply_axis_limits",
    "draw_grid",
    "draw_axis_tick_labels",
    "draw_axis_labels",
    "draw_title",
    "hide_main_ticks",
    "style_main_spines",
    "draw_legend",
]
