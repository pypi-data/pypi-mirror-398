import itertools
from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Iterable, Iterator, Optional

import matplotlib.pyplot as plt
import numpy as np

Renderer = Callable[[plt.Axes, np.ndarray, np.ndarray], None]


def render_line(ax, x, y, color: str = "tab:blue", linewidth: float = 2, **plot_kwargs):
    ax.plot(x, y, color=color, linewidth=linewidth, **plot_kwargs)


def render_scatter(ax, x, y, **scatter_kwargs):
    default = dict(color="tab:orange", s=50, alpha=0.7, edgecolors="black")
    default.update(scatter_kwargs)
    ax.scatter(x, y, **default)


def render_bar(ax, x, y, **bar_kwargs):
    width = bar_kwargs.pop("width", None)
    if width is None:
        if len(x) > 1:
            diffs = np.diff(np.sort(x))
            positive_diffs = diffs[diffs > 0]
            step = positive_diffs.min() if len(positive_diffs) else 1.0
        else:
            step = 1.0
        width = step * 0.8
    default = dict(color="tab:green", alpha=0.6, width=width)
    default.update(bar_kwargs)
    ax.bar(x, y, **default)


@dataclass
class SeriesSpec:
    """
    単系列の情報をまとめるコンテナ。
    x, y: データ
    renderer: 使用するレンダラー関数
    ラベルや色などは指定があれば優先し、なければcolor cycleを利用する。
    """

    DEFAULT_COLORS: ClassVar[list[str]] = [
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
        "tab:pink",
        "tab:gray",
        "tab:olive",
        "tab:cyan",
    ]
    DEFAULT_LINESTYLES: ClassVar[list[str]] = ["-", "--", "-.", ":"]
    x: np.ndarray
    y: np.ndarray
    renderer: Renderer = render_line
    label: Optional[str] = None
    color: Optional[str] = None
    linestyle: Optional[str] = None
    marker: Optional[str] = None
    linewidth: Optional[float] = None
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.x) != len(self.y):
            raise ValueError("Length of x and y must match in SeriesSpec.")

    def to_kwargs(self, default_color: Optional[str] = None, default_linestyle: Optional[str] = None) -> dict[str, Any]:
        merged = dict(self.kwargs)
        if self.color is not None:
            merged.setdefault("color", self.color)
        elif default_color is not None:
            merged.setdefault("color", default_color)
        if self.linestyle is not None:
            merged.setdefault("linestyle", self.linestyle)
        elif default_linestyle is not None:
            merged.setdefault("linestyle", default_linestyle)
        if self.marker is not None:
            merged.setdefault("marker", self.marker)
        if self.linewidth is not None:
            merged.setdefault("linewidth", self.linewidth)
        if self.label is not None:
            merged.setdefault("label", self.label)
        return merged


def _color_cycle(ax: plt.Axes) -> Iterator[str]:
    """
    なるべく公開APIに近い形で色サイクルを取得する。
    Axes固有のサイクルがあればそれを優先し、無ければ rcParams を使う。
    """
    try:
        prop_cycler = ax._get_lines.prop_cycler  # type: ignore[attr-defined]
        colors = prop_cycler.by_key().get("color", [])
        if colors:
            return itertools.cycle(colors)
    except Exception:
        pass
    try:
        prop_cycler = plt.rcParams.get("axes.prop_cycle")
        if prop_cycler is not None:
            colors = prop_cycler.by_key().get("color", [])
            if colors:
                return itertools.cycle(colors)
    except Exception:
        pass
    return itertools.cycle(SeriesSpec.DEFAULT_COLORS)


def render_multi(
    ax: plt.Axes,
    series_specs: Iterable[SeriesSpec],
    *,
    use_color_cycle: bool = True,
) -> None:
    """
    単系列用レンダラーを組み合わせて複数系列を描く薄いラッパー。
    use_color_cycle: 色指定がないSeriesでcolor cycleを利用するか。
    """
    color_cycle = _color_cycle(ax) if use_color_cycle else None
    linestyle_cycle = itertools.cycle(SeriesSpec.DEFAULT_LINESTYLES)
    series_list = list(series_specs)
    for idx, spec in enumerate(series_list):
        default_color = None
        if color_cycle:
            try:
                default_color = next(color_cycle)
            except StopIteration:
                default_color = None
        if default_color is None and SeriesSpec.DEFAULT_COLORS:
            default_color = SeriesSpec.DEFAULT_COLORS[idx % len(SeriesSpec.DEFAULT_COLORS)]
        default_linestyle = next(linestyle_cycle)
        kwargs = spec.to_kwargs(default_color=default_color, default_linestyle=default_linestyle)
        spec.renderer(ax, spec.x, spec.y, **kwargs)


__all__ = [
    "Renderer",
    "render_line",
    "render_scatter",
    "render_bar",
    "SeriesSpec",
    "render_multi",
]
