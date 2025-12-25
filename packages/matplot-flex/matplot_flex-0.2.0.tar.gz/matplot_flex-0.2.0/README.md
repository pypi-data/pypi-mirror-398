# Matplot Flex
[![CI](https://github.com/obitsu-jo/matplot-flex/actions/workflows/ci.yml/badge.svg)](https://github.com/obitsu-jo/matplot-flex/actions/workflows/ci.yml)

モジュール化されたサブプロット構成、テキストのフィット、基本レンダラーをまとめた Matplotlib 補助ライブラリです。

## インストール（PyPI）
```
pip install matplot-flex
```

未公開の場合は GitHub から直接インストールできます。
```
pip install "matplot-flex @ git+https://github.com/obitsu-jo/matplot-flex.git"
```

## 対応環境
- Python 3.10 以上

## クイックスタート
```python
import numpy as np
from matplot_flex import (
    AxisConfig, LegendConfig, LegendItem, SeriesSpec,
    plot_template, divide_fig_ratio, draw_graph_module, plot_on_module,
    render_line, render_multi,
)

fig, figs = plot_template("My Plot")
left_fig, right_fig = divide_fig_ratio(figs[1], "horizontal", ratios=[1, 1])

x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
series = [
    SeriesSpec(x=x, y=y1, renderer=render_line, label="sin"),
    SeriesSpec(x=x, y=y2, renderer=render_line, label="cos", linestyle="--"),
]
legend_items = [
    LegendItem(label="sin", color="tab:blue"),
    LegendItem(label="cos", color="tab:orange", linestyle="--"),
]

module = draw_graph_module(left_fig)
plot_on_module(
    module,
    x,
    y1,
    "Sine & Cosine",
    renderer=lambda ax, xx, yy: render_multi(ax, series),
    x_axis=AxisConfig(label="x"),
    y_axis=AxisConfig(label="value"),
    legend=LegendConfig(items=legend_items, position="upper center", offset=(0.0, 0.02)),
    series_specs=series,  # ensures axes cover all series
)

fig.savefig("example.png", dpi=220)
```

## 構成
- `matplot_flex/config.py`: 軸/凡例/グリッド設定（`AxisConfig.pad` による余白指定を含む）。
- `matplot_flex/axes_utils.py`: Figure/SubFigure の主Axes取得ヘルパ。
- `matplot_flex/text_utils.py`: テキストフィット、パラメータ整形、角丸フレーム（zorder指定）、日付/指数フォーマッタ。
- `matplot_flex/renderers.py`: 折れ線/散布/棒グラフ、複数系列補助、`SeriesSpec`。
- `matplot_flex/layout.py`: Figure/SubFigure 生成と分割ユーティリティ。
- `matplot_flex/decorators.py`: 目盛/ラベル/グリッドなどの装飾処理。
- `matplot_flex/templates.py`: `plot_template` / `plot_on_module` の合成処理。
- `main.py`: `modular_subplot_example.png` を生成するサンプル。
- `smoke_test.py`: 生成確認の簡易テスト。

公開APIは `matplot_flex/__init__.py` から再エクスポートしています。  
詳細なAPIノートは `matplot_flex/README.md`、完全仕様は `docs/full_reference.md` を参照してください。

## サンプルの実行
```
python main.py
```
リポジトリ直下に `modular_subplot_example.png` を出力します。

## CI
GitHub Actions で `python smoke_test.py` を実行します。

## テスト
```
python smoke_test.py
```
PNG を再生成して、生成できたことを確認します。

```
python -m pytest -q
```
代表的な利用パターンの描画が通ることを確認します。

## 依存関係の方針
ライブラリ利用向けの範囲指定は `pyproject.toml` で管理し、開発・CI の再現性は `requirements.txt` の固定版で担保します。

開発環境の導入:
```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## バージョニング方針
SemVer（MAJOR.MINOR.PATCH）に従います。変更履歴は `CHANGELOG.md` を参照してください。

- MAJOR: 互換性のない変更
- MINOR: 後方互換のある機能追加
- PATCH: 後方互換のあるバグ修正

## ローカルパッケージとして導入（再利用向け）
```
pip install -e .
```
以降は同一環境の別ディレクトリから `import matplot_flex` できます。

## PyPI 公開手順
1. PyPI のアカウント作成と 2FA 設定
2. `pyproject.toml` の `version` を更新
3. 配布物を作成
```
python -m build
```
4. PyPI にアップロード
```
python -m twine upload dist/*
```

## 更新手順（リリース）
1. 変更を反映
2. `pyproject.toml` の `version` を更新
3. `CHANGELOG.md` に変更内容を追記
4. テストを実行
```
python -m pytest -q
```
5. ビルドとアップロード
```
rm -rf dist/
python -m build
python -m twine upload dist/*
```
6. 任意でタグを付ける
```
git tag vX.Y.Z
git push origin vX.Y.Z
```

## ライセンス
MIT License（`LICENSE` を参照）
