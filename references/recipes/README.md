# 图型配方

配方已按领域拆分。机器绘图时先读 [figure-catalog](../figure-catalog.md)，
再进入对应领域；完整可运行脚本仍以 [templates](../../templates/) 为准。

## 0. 通用参数块

```python
from pathlib import Path


def main():
    # ---------- 输出 ----------
    output_png = Path("figures/Fig_01.png")

    # ---------- 区域 ----------
    lon_min, lon_max = 112.0, 132.0
    lat_min, lat_max = 17.0, 32.5

    # ---------- 色标 ----------
    cmap_name = "cmo.balance"
    vmin, vmax = -0.25, 0.25
    cbar_extend = "both"
    cbar_label = "SSH anomaly (m)"

    # ---------- 版面 ----------
    fig_width, fig_height = 7.2, 5.0
    font_tick, font_label, font_title = 8, 9, 10
    save_dpi = 300
```

## 配方索引

| 领域 | 文件 | 图型 |
|---|---|---|
| 地图配方 | [maps.md](maps.md) | 单张区域地图、多面板地图（共用色标）、相位、地形 + 陆架坡折 |
| 剖面与 Hovmöller 配方 | [sections.md](sections.md) | Hovmöller 图、垂向剖面 |
| 时间序列配方 | [time-series.md](time-series.md) | 时间序列 + 标准差 |
| 散点与属性图配方 | [statistics.md](statistics.md) | 散点 / 属性图 |
| 谱分析配方 | [spectral.md](spectral.md) | FFT 频谱 |
| 流场与轨迹配方 | [flow.md](flow.md) | Quiver（流场/力场）、粒子轨迹 / LineCollection |
