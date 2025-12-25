from typing import Any, Callable, Optional

import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from .axes_utils import get_primary_axes


def draw_rounded_frame(fig, bg_color: str = "#eeeeee", edge_color: str = "black", zorder: float = -1) -> None:
    """
    Figure(またはSubFigure)の領域いっぱいに、自動で角丸の矩形を描画する。
    """
    ax = get_primary_axes(fig, hide_axis_on_create=True)

    fancy_box = patches.FancyBboxPatch(
        (0, 0),
        1.0,
        1.0,
        boxstyle="round,pad=0,rounding_size=0.02",
        facecolor=bg_color,
        edgecolor=edge_color,
        linewidth=2,
        mutation_scale=1,
        transform=ax.transAxes,
        clip_on=False,
        zorder=zorder,
    )
    ax.add_patch(fancy_box)


def format_params(params: dict) -> str:
    """
    辞書を受け取り、Matplotlib標準で表示可能な複数行の数式文字列を返す。
    例: "$a = 1.00$\n$b = 0.50$"
    """
    lines = [r"$\mathbf{Parameters}:$"]
    for k, v in params.items():
        clean_k = k.replace("_", r"\_")
        val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
        lines.append(rf"${clean_k} = {val_str}$")
    return "\n".join(lines)


def draw_text(
    ax: plt.Axes,
    text: str,
    *,
    mode: str = "fit",
    x: float = 0.5,
    y: float = 0.5,
    transform: Optional[Any] = None,
    fontsize: float = 12.0,
    min_fontsize: float = 4.0,
    max_fontsize: float = 48.0,
    padding: float = 0.8,
    ha: str = "center",
    va: str = "center",
    rotation: float = 0.0,
    color: str = "black",
    fontweight: str = "normal",
    target_bbox: Optional[Any] = None,
    zorder: Optional[float] = None,
) -> plt.Text:
    """
    汎用テキスト描画。mode="fixed" なら指定フォントサイズ、"fit" なら枠に収まるよう自動調整。
    target_bbox を省略すると Axes 全体にフィットする。
    """
    if transform is None:
        transform = ax.transAxes

    text_kwargs = dict(
        ha=ha,
        va=va,
        rotation=rotation,
        fontsize=fontsize,
        color=color,
        fontweight=fontweight,
        transform=transform,
    )
    if zorder is not None:
        text_kwargs["zorder"] = zorder
    t = ax.text(x, y, text, **text_kwargs)
    if mode == "fixed":
        return t

    fig = ax.get_figure()
    if fig.canvas.get_renderer() is None:
        fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox_text = t.get_window_extent(renderer)
    bbox_target = target_bbox or ax.get_window_extent(renderer)
    if bbox_text.width == 0 or bbox_text.height == 0:
        return t

    width_ratio = bbox_target.width / bbox_text.width
    height_ratio = bbox_target.height / bbox_text.height
    scale = min(width_ratio, height_ratio) * padding
    new_size = fontsize * scale
    new_size = max(min_fontsize, min(max_fontsize, new_size))
    t.set_fontsize(new_size)
    return t


def draw_text_on_fig(fig, text: str, **kwargs) -> plt.Text:
    """
    Figure/SubFigure から主Axesを取得し、その上に draw_text を適用する。
    """
    ax = get_primary_axes(fig, hide_axis_on_create=True)
    return draw_text(ax, text, **kwargs)


def sci_formatter(decimals: int = 1) -> Callable[[float], str]:
    """指数表記を返すフォーマッタのファクトリ"""
    def _fmt(val: float) -> str:
        return f"{val:.{decimals}e}"
    return _fmt


def date_formatter(fmt: str = "%Y-%m-%d") -> Callable[[float], str]:
    """matplotlib日付番号を文字列に変換するフォーマッタのファクトリ"""
    def _fmt(val: float) -> str:
        return mdates.num2date(val).strftime(fmt)
    return _fmt


__all__ = [
    "draw_rounded_frame",
    "format_params",
    "draw_text",
    "draw_text_on_fig",
    "sci_formatter",
    "date_formatter",
]
