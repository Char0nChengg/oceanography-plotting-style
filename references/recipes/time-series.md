# 时间序列配方

> 通用参数块见 [recipes/README.md](README.md#0-通用参数块)；
> 图型总目录见 [figure-catalog.md](../figure-catalog.md)。

## 1. 时间序列 + 标准差

数据契约：`dates`、`mean`、`std` 已按同一时间基准对齐。

```python
import matplotlib.pyplot as plt

from ocean_plot import auto_time_axis, check_figure, save_figure

fig, ax = plt.subplots(figsize=(fig_width, 2.8), constrained_layout=True)
ax.fill_between(dates, mean - std, mean + std,
                color="C0", alpha=0.22, linewidth=0)
ax.plot(dates, mean, color="C0", linewidth=1.3, label="Ensemble mean")
ax.set_ylabel("SSH (m)", fontsize=font_label)
ax.legend(frameon=False, loc="upper right", fontsize=font_tick)
auto_time_axis(ax, dates)
ax.tick_params(labelsize=font_tick)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

- `mean`/`std` 必须已经按同一时间轴对齐；不要用不同长度的 `dates` 广播。
- 滚动统计的 `center=True` 会在两端产生 NaN；如果不想显示断头，明确用 `min_periods` 或裁掉两端，而不是偷偷 `interpolate()`。
