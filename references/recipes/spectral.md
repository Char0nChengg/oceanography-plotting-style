# 谱分析配方

> 通用参数块见 [recipes/README.md](README.md#0-通用参数块)；
> 图型总目录见 [figure-catalog.md](../figure-catalog.md)。

## 1. FFT 频谱

数据契约：`x` 为一维序列，`time_seconds` 为同长度的秒/天单位采样时间；两者必须等长。

```python
import matplotlib.pyplot as plt
import numpy as np

from ocean_plot import check_figure, save_figure
from ocean_spectral import ar1_threshold

time_seconds = np.asarray(time_seconds, dtype=float)
steps = np.diff(time_seconds)
if not np.allclose(steps, np.median(steps), rtol=1e-6, atol=1e-9):
    raise ValueError("FFT needs regular sampling; interpolate or use Lomb–Scargle")
dt = float(np.median(steps))

result = ar1_threshold(
    x, dt=dt, confidence=0.95, n_sim=500, seed=0,
    detrend="linear", window="hann",
)
freq, amp = result["frequency"], result["amplitude"]
threshold = result["threshold"]
positive = freq > 0

fig, ax = plt.subplots(figsize=(fig_width, 3.0), constrained_layout=True)
ax.plot(freq[positive], amp[positive], color="C0", linewidth=1.0, label="Amplitude")
ax.plot(freq[positive], threshold[positive], color="C3",
        linestyle="--", linewidth=1.0, label="AR(1) 95% threshold")
ax.set_xscale("log")
ax.set_xlabel("Frequency (cycles per day)", fontsize=font_label)
ax.set_ylabel("Amplitude", fontsize=font_label)
ax.tick_params(labelsize=font_tick)
ax.legend(frameon=False, fontsize=font_tick)

for period, color in zip([2, 5, 10, 20], ["0.6", "0.5", "0.4", "0.3"]):
    ax.axvline(1 / period, color=color, linestyle=":", linewidth=0.8)
    ax.text(1 / period, ax.get_ylim()[1] * 0.95, f"{period} d",
            rotation=90, va="top", ha="right", fontsize=font_tick, color=color)

for issue in check_figure(fig, check_bounds=True):
    print("layout warning:", issue)
save_figure(fig, output_png, dpi=save_dpi, also_pdf=True, tight=False)
```

- `dt` 必须来自规则采样；有缺测时先插值或改用 Lomb–Scargle，不要直接对不等间隔样本做 FFT。
- 窗函数和归一化方式会改变纵轴数值；图注写清楚。
- `ar1_threshold()` 是一个**明确的零假设检验**（AR(1) 红噪声 + Monte-Carlo），不是万能显著性；方法部分写清 `n_sim`、`confidence`、窗函数和去趋势方式。
- 频率轴用对数时，周期标注放在顶部要防止重叠。
