# 散点与属性图配方

> 通用参数块见 [recipes/README.md](README.md#0-通用参数块)；
> 图型总目录见 [figure-catalog.md](../figure-catalog.md)。

## 1. 散点 / 属性图

数据契约：`x`、`y`、`values` 长度一致。

```python
import matplotlib.pyplot as plt

from ocean_plot import check_figure, get_cmap, save_figure

fig, ax = plt.subplots(figsize=(fig_width, 4.0), constrained_layout=True)
sc = ax.scatter(
    x, y, c=values, cmap=get_cmap("cmo.dense"),
    s=6, edgecolors="none", vmin=vmin, vmax=vmax,
)
cbar = fig.colorbar(sc, ax=ax, extend="neither")
cbar.set_label("Amplitude (m)", fontsize=font_label)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

- `cmap` 传的是 colormap 对象，不是字符串；用 `get_cmap("cmo.dense")` 或 `cmocean.cm.dense`。
- 散点太密时用 `rasterized=True` 或六边形分箱，不要靠把 `s` 调到 0.1 掩盖过绘制。
