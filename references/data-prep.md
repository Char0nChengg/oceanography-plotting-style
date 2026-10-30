# 数据准备：维度、区域、经度、滤波

绘图错误里很大一部分不是 `matplotlib` 的问题，而是坐标/维度在进入绘图函数前就已经错了。这个文件给出进入绘图前的检查顺序；具体实现以 `ocean_data.py` 为准，不再维护第二份代码。

## 1. 读取与维度统一

### 1.1 先看，不要先改名

```python
from pathlib import Path

import xarray as xr

path = Path("data/ssh.nc")  # replace with your file
with xr.open_dataset(path, decode_times=True, mask_and_scale=True) as ds:
    print(ds)
    print(ds.dims)
    for name in ds.coords:
        print(name, ds[name].dims, ds[name].shape, ds[name].attrs.get("units"))
    for name in ds.data_vars:
        print(name, ds[name].dims, ds[name].shape, ds[name].attrs.get("units"))
```

先确认：

- 经纬度是 **1D 规则坐标**还是 **2D 曲线坐标**；
- `x/y` 是经纬度别名，还是投影坐标（单位 m/km）；
- `depth/lev` 的单位是 m 还是 cm，正方向朝上还是朝下；
- `time` 是 `datetime64`、`cftime` 还是数值（年/月/日序号）；
- 变量是否含 `time` 维，是否多文件、是否有 ensemble 维。

### 1.2 统一维度名

```python
from ocean_data import canonicalize_dims, load_for_plot, pick_var

ds = canonicalize_dims(ds)
da = pick_var(ds, "ssh")
```

`canonicalize_dims()` 只映射语义明确的别名；`x/y` 只有在单位不是 m/km 时才可能改名，并在无法判断时警告。已有 `lon`/`latitude` 等标准名时，不会再用别名覆盖。改完名后必须再看一次 `ds.dims`。

变量名不确定时先诊断：

```bash
ocean-plot --inspect data.nc
```

```python
from ocean_vocab import inspect_dataset, resolve_variable

print(inspect_dataset(ds).as_dict())
name = resolve_variable(ds, "u_surface")   # 歧义时列出候选，不静默选择
```

更完整的 CF/profile 说明见 [netcdf-profiles.md](netcdf-profiles.md)。

`pick_var()` 支持的常见语义：

```text
ssh       -> ssh, zos, sla, adt, sea_surface_height
u_current -> u, uo, water_u, eastward_sea_water_velocity
v_current -> v, vo, water_v, northward_sea_water_velocity
u_surface -> uos, usurface, surface_u
v_surface -> vos, vsurface, surface_v
temp      -> temp, thetao, temperature, sea_water_temperature
salt      -> salt, so, salinity, sea_water_salinity
```

不要静默 `isel(time=0)`。如果确实只要第一帧，明确写 `da = da.isel(time=0)` 并在图注或回复里说明；时间平均写 `da.mean("time")`；Hovmöller 保留 `time`。

### 1.3 一步读取

```python
da = load_for_plot(
    path,
    "ssh",
    region={"lon": (112, 132), "lat": (17, 32.5)},
)
```

`load_for_plot()` 默认保留时间维，并在关闭文件前 `.load()`。如果数据还有 ensemble/member 维，先明确 `mean("member")` 或选一个成员，不要让绘图函数猜。

## 2. 经纬度处理

### 2.1 0–360 与 −180–180

```python
import numpy as np
from ocean_data import to_0_360, to_minus180

lon_0_360 = to_0_360(np.asarray(lon))
lon_minus180 = to_minus180(np.asarray(lon))
```

- 绘图前确定一种约定；不要一半数据 0–360、另一半 −180–180。
- 区域边界跨日界线（如 170°E–170°W）时，不要直接 `slice(170, -170)`；用 `subset_region()`。
- **1D** 负经度或跨日界线区域会返回展开后的 0–360 坐标，可能大于 360；此时用 `ccrs.PlateCarree(central_longitude=180)` 或等价投影，并在图注说明。
- **2D** 曲线坐标只做布尔掩膜，保留原生坐标，不 unwrap、不排序；跨日界线时使用与原生坐标匹配的投影。
- 全图范围 `(-180, 180)` 或 `(0, 360)` 不会裁掉经度；1D 会在需要时归一化到 0–360。

### 2.2 纬度升/降序

```python
ds = ds.sortby("lat")   # 1D 纬度统一升序
```

如果原始纬度是降序，`slice(lat_min, lat_max)` 可能返回空；先排序再裁剪。2D 纬度不能简单 `sortby`，用掩膜。

### 2.3 区域裁剪

优先用 `.sel`，不要用 `isel` + 布尔数组；后者在坐标降序、2D 坐标、跨日界线下很容易出错。项目里已经提供了测试过的实现：

```python
from ocean_data import subset_region

ds = subset_region(ds, lon_bounds=(112, 132), lat_bounds=(17, 32.5))
```

语义：

- 1D 经纬度：排序、降序纬度、负经度、跨日界线；
- 2D 曲线经纬度：布尔掩膜，保留 NaN，不改变原生经度；
- 跨日界线/负经度的 1D 区域：返回单调展开的 0–360° 经度，可能 >360；
- 全图范围：不裁经度；1D 在边界使用负经度或 >180 时归一化到 0–360；
- 空区域：给出数据实际范围并抛 `ValueError`。

如果数据是 ROMS 交错网格、非结构三角网格或投影坐标，不要强行套这个函数；保留原生坐标并用对应投影。

### 2.4 最小流水线

```python
import xarray as xr
from ocean_data import canonicalize_dims, grid_arrays, pick_var, subset_region
from ocean_plot import validate_grid

with xr.open_dataset(path, decode_times=True, mask_and_scale=True) as ds:
    ds = canonicalize_dims(ds)
    ds = subset_region(ds, (112, 132), (17, 32.5))
    da = pick_var(ds, "ssh")
    da = da.load()

# 单帧地图；时间平均用 da.mean("time")；Hovmöller 保留 time 维
frame = da.isel(time=0) if "time" in da.dims else da
lon, lat, data = grid_arrays(frame)
validate_grid(lon, lat, data, name="ssh")
```

`grid_arrays()` 支持两种常见布局：

- 1D 坐标挂在 `y/x` 维上：`lon(x)`、`lat(y)`；
- 2D 曲线坐标：`lon(y, x)`、`lat(y, x)`。

它只把空间维移到末尾，不猜变量含义；含 `time/depth` 的数据仍保留前导维。

## 3. 形状与广播校验

在调用 `pcolormesh`/`contourf` 前做一次显式检查：

```python
from ocean_plot import validate_grid

info = validate_grid(lon, lat, data, name="ssh")
print(info)
```

规则：

- 1D `lon` + 1D `lat` + 2D `data`：`data.shape[-2:] == (lat.size, lon.size)`。
- 2D `lon` + 2D `lat` + 2D `data`：`data.shape[-2:] == lon.shape == lat.shape`；前面可以有 `time/depth` 等前导维。
- 如果 `lon` 是 `(n,)`、`lat` 是 `(m,)`、`data` 是 `(n,)`，这不是地图数据；不要靠广播硬画。
- 用 `np.meshgrid(lon, lat)` 时确认 `indexing="xy"`，并检查结果形状是 `(lat, lon)`。
- 2D 坐标不是规则网格时，`pcolormesh` 仍可用，但不要对它做 `sortby("lon")`。

## 4. 滤波与掩膜

### 4.1 IQR（带保护）

```python
from ocean_data import iqr_filter

clean = iqr_filter(values, factor=1.5)
```

- 默认返回副本；`copy=False` 才会原地修改。
- 常数场、量化场（IQR=0）原样返回，不能把有效数据全清空。
- IQR 只适合作为异常值筛查，不应替代物理掩膜。

### 4.2 最大连通区域

```python
from ocean_data import keep_largest_region

clean = keep_largest_region(values, connectivity=2)
```

- 默认 8 连通（`connectivity=2` 或 `8`）；4 连通用 `1`/`4`。
- 跨日界线的连通区域需要把经度首尾拼接后再标记，不能直接套这个函数。
- 这些函数默认返回副本；如果原地修改，调用方必须知道。

### 4.3 振幅掩膜

```python
import numpy as np
import xarray as xr
from ocean_data import iqr_filter, keep_largest_region


def get_amplitude_mask(path, var="amplitude"):
    with xr.open_dataset(path) as ds:
        amp = np.asarray(ds[var].values, dtype=float).copy()
    amp[amp < 0] = np.nan
    amp = iqr_filter(amp)
    amp = keep_largest_region(amp)
    return np.isfinite(amp)
```

用 `with` 确保异常时也关闭文件；不要在 `ds.close()` 之前返回惰性数组。

## 5. 时间轴

- `datetime64` / pandas `Timestamp`：直接交给 Matplotlib。
- 数值时间（如 0.5 年）：用 `MaxNLocator`，不要套 `DateFormatter`；`auto_time_axis()` 会重置为数值 formatter。
- `cftime`（NoLeap、360_day 等）：`auto_time_axis()` 会警告并用 Gregorian 近似；需要日历精确时用 `nc_time_axis` 或转成数值年份/月并明确标注。
- 多文件拼接：`xr.open_mfdataset(paths, combine="by_coords")` 后检查时间是否重复/乱序。
- 画图前检查 `np.diff(time)` 是否规则；FFT/谱分析对缺测和不规则采样非常敏感，缺测应插值或改用 Lomb–Scargle。

## 6. CSV、滑动平均、相位

```python
from pathlib import Path

import pandas as pd

path = Path("data/series.csv")
df = pd.read_csv(path, parse_dates=["release_date"]).sort_values("release_date")
df = df.set_index("release_date")
df["rolling_mean"] = df["value"].rolling(window=30, center=True, min_periods=15).mean()
df["rolling_std"] = df["value"].rolling(window=30, center=True, min_periods=15).std()
```

假设 `phase_rad` 已从数据中读取为弧度数组：

```python
import numpy as np

phase_deg = (np.rad2deg(phase_rad) + 360.0) % 360.0
```

- 滑动窗口要按采样频率定义，不要对所有数据都写 30；日数据 30 d、月数据 12 month 的含义不同。
- 相位是循环量；`0°` 与 `360°` 等价，色标首尾要一致。

## 7. 常见数据错误

| 现象 | 根因 | 处理 |
|---|---|---|
| 图上下颠倒 | 纬度降序 / 深度正方向反了 | `sortby("lat")`；确认 depth 正负后再 `invert_yaxis` |
| 图左右断裂 | 经度 0–360 与 −180–180 混用 | 统一约定；1D 用 `subset_region` 展开 |
| 区域裁剪为空 | 降序坐标 + `slice` | 先排序；打印数据范围 |
| 地图只有一条边 | `lon`/`lat` 与 `data` 形状 broadcast 错 | `validate_grid` |
| 色标全是一个颜色 | `vmin/vmax` 没覆盖数据，或全 NaN | 打印 `nanmin/nanmax/nanpercentile` |
| 陆地也被填色 | 没有 land mask / 没画陆地 | 用 `where` 掩膜或叠加 `cfeature.LAND` |
| 时间轴变成 1970 | 数值时间被当 datetime | 明确时间类型，别强转 |
| 关闭文件后数组失效 | 惰性 dask 数组 + `close()` | 先 `.load()` 或 `.compute()` |
| 全图缺经度 | 全图边界被当成跨日界线 | 用修复后的 `subset_region`，并加全图测试 |
