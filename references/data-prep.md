# 数据准备：维度、区域、经度、滤波

绘图错误里很大一部分不是 `matplotlib` 的问题，而是坐标/维度在进入绘图函数前就已经错了。这个文件给出进入绘图前的检查顺序。

## 1. 读取与维度统一

### 1.1 先看，不要先改名

```python
import xarray as xr

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

只映射语义明确的别名；`x/y` 只有在确认是经纬度时才改名。

```python
DIM_ALIASES = {
    "lon": {"lon", "longitude", "xlon", "x"},
    "lat": {"lat", "latitude", "ylat", "y"},
    "time": {"time", "t", "date", "Time"},
    "depth": {"depth", "z", "lev", "level", "DEPTH"},
}

def canonicalize_dims(ds):
    rename = {}
    names = list(ds.dims) + [c for c in ds.coords if c not in ds.dims]
    for std, aliases in DIM_ALIASES.items():
        matches = [n for n in names if n.lower() in {a.lower() for a in aliases}]
        if not matches:
            continue
        if std in matches:
            # 已有标准名，其他别名不再改名，避免 lon/longitude 冲突
            continue
        source = matches[0]
        # x/y 若带投影单位，不能当经纬度
        if source.lower() in {"x", "y"}:
            units = str(ds[source].attrs.get("units", "")).lower()
            if units in {"m", "km", "meter", "metre"}:
                continue
        rename[source] = std
    if rename:
        ds = ds.rename(rename)
    return ds
```

注意：

- 如果 `lon` 和 `longitude` 同时存在，保留 `lon`，不要 `rename({"longitude": "lon"})`，那会直接冲突。
- 如果 `x/y` 是投影坐标（如 `x=... m`），不要改名；用对应的 Cartopy 投影绘图。
- 改完名后，用 `ds.dims` 再确认一次，不要假设。

### 1.3 变量别名

```python
VAR_ALIASES = {
    "ssh": ("ssh", "zos", "sla", "adt", "sea_surface_height"),
    "u": ("u", "uo", "water_u", "eastward_sea_water_velocity"),
    "v": ("v", "vo", "water_v", "northward_sea_water_velocity"),
    "temp": ("temp", "thetao", "temperature", "sea_water_temperature"),
    "salt": ("salt", "so", "salinity", "sea_water_salinity"),
}

def pick_var(ds, key):
    for name in VAR_ALIASES.get(key, (key,)):
        if name in ds:
            return ds[name]
    raise KeyError(f"找不到 {key}；可用变量: {list(ds.data_vars)}")
```

不要静默 `isel(time=0)`。如果确实只要第一帧，明确写 `da = da.isel(time=0)` 并在图注/回复里说明；如果要时间平均，写 `da.mean("time")`；如果要 Hovmöller，保留 `time`。

## 2. 经纬度处理

### 2.1 0–360 与 −180–180

```python
def to_minus180(lon):
    return ((lon + 180.0) % 360.0) - 180.0

def to_0_360(lon):
    return lon % 360.0
```

- 绘图前确定一种约定；不要一半数据 0–360、另一半 −180–180。
- 区域边界跨日界线（如 170°E–170°W）时，先转成 −180–180，再分段选取，不要直接 `slice(170, -170)`（会得到空集）。
- 2D 经度也能转换，但转换后可能不再单调；2D 曲线坐标用布尔掩膜，不要 `sortby`。

### 2.2 纬度升/降序

```python
ds = ds.sortby("lat")   # 统一升序；绘图前确认
```

如果原始纬度是降序，`slice(lat_min, lat_max)` 可能返回空；先排序再裁剪。2D 纬度不能简单 `sortby`，用掩膜。

### 2.3 区域裁剪

优先用 `.sel`，不要用 `isel` + 布尔数组；后者在坐标降序、2D 坐标、跨日界线下很容易出错。项目里已经提供了测试过的实现：

```python
from ocean_data import subset_region

ds = subset_region(ds, lon_bounds=(112, 132), lat_bounds=(17, 32.5))
```

它处理：

- 1D 经纬度：排序、降序纬度、负经度、跨日界线；
- 2D 曲线经纬度：布尔掩膜，保留 NaN；
- 跨日界线/负经度：返回单调展开的 0–360° 经度，可能 >360；绘图时用 `ccrs.PlateCarree(central_longitude=180)` 或等价投影，并在图注说明；
- 空区域：给出数据实际范围并抛 `ValueError`。

如果数据是 ROMS 交错网格、非结构三角网格或投影坐标，不要强行套这个函数；保留原生坐标并用对应投影。

### 2.4 一条最小流水线

```python
import xarray as xr
from ocean_data import canonicalize_dims, load_for_plot, pick_var, subset_region
from ocean_plot import validate_grid

with xr.open_dataset(path, decode_times=True, mask_and_scale=True) as ds:
    ds = canonicalize_dims(ds)
    ds = subset_region(ds, (112, 132), (17, 32.5))
    da = pick_var(ds, "ssh")

    # 明确选择时间：不要静默 isel(time=0)
    # 单帧：da = da.isel(time=0)
    # 时间平均：da = da.mean("time")
    # 保留时间（Hovmöller/时间序列）：不动 time 维
    da = da.load()

# 关闭文件后再画图；da 已加载
validate_grid(da["lon"], da["lat"], da.isel(time=0) if "time" in da.dims else da)
```

或者一步到位：

```python
da = load_for_plot(path, "ssh", region={"lon": (112, 132), "lat": (17, 32.5)})
```

如果 `da` 还有 ensemble/member 维，先明确 `mean("member")` 或选一个成员；不要让绘图函数猜。

## 3. 形状与广播校验

在调用 `pcolormesh`/`contourf` 前做一次显式检查：

```python
from ocean_plot import validate_grid

info = validate_grid(lon, lat, data, name="ssz")
print(info)
```

规则：

- 1D `lon` + 1D `lat` + 2D `data`：`data.shape[-2:] == (lat.size, lon.size)`。
- 2D `lon` + 2D `lat` + 2D `data`：三者形状完全一致。
- 含时间/深度的数据：`data.shape[-2:]` 仍必须是 `(lat, lon)`；前面可以有 `time`、`depth` 等维。
- 如果 `lon` 是 `(n,)`、`lat` 是 `(m,)`、`data` 是 `(n,)`，这不是地图数据；不要靠广播硬画。
- 用 `np.meshgrid(lon, lat)` 时确认 `indexing="xy"`，并检查结果形状是 `(lat, lon)`。

## 4. 滤波与掩膜

### 4.1 IQR（带保护）

```python
import numpy as np

def iqr_filter(values, factor=1.5, copy=True):
    arr = np.array(values, dtype=float, copy=copy)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return arr
    q1, q3 = np.percentile(finite, [25, 75])
    iqr = q3 - q1
    if not np.isfinite(iqr) or iqr <= 0:
        return arr  # 常数场/量化场：不能把所有值清空
    lower, upper = q1 - factor * iqr, q3 + factor * iqr
    arr[(arr < lower) | (arr > upper)] = np.nan
    return arr
```

### 4.2 最大连通区域

```python
from scipy.ndimage import label

def keep_largest_region(values, connectivity=2, copy=True):
    arr = np.array(values, dtype=float, copy=copy)
    mask = np.isfinite(arr)
    if not mask.any():
        return arr
    structure = np.ones((3, 3), dtype=int) if connectivity == 2 else None
    lab, n = label(mask, structure=structure)
    if n == 0:
        return arr
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    arr[lab != sizes.argmax()] = np.nan
    return arr
```

- 默认 8 连通（`connectivity=2`）适合海洋斑块；4 连通会把对角相连的区域切开。
- 跨日界线的连通区域需要把经度首尾拼接后再标记，不能直接套这个函数。
- 这些函数默认返回副本；如果原地修改，调用方必须知道。

### 4.3 振幅掩膜

```python
import xarray as xr

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
- `cftime`（NoLeap、360_day 等）：不要 `pd.Timestamp(cftime_obj)`；用 `nc_time_axis`，或转成数值年份/月，并明确标注“非标准日历”。
- 数值时间（如 0.5 年）：用 `MaxNLocator`，不要套 `DateFormatter`。
- 多文件拼接：`xr.open_mfdataset(..., combine="by_coords")` 后检查时间是否重复/乱序。
- 画图前检查 `np.diff(time)` 是否规则；FFT/谱分析对缺测和不规则采样非常敏感。

## 6. CSV、滑动平均、相位

```python
import pandas as pd

df = pd.read_csv(path, parse_dates=["release_date"]).sort_values("release_date")
df = df.set_index("release_date")
df["rolling_mean"] = df["value"].rolling(window=30, center=True, min_periods=15).mean()
df["rolling_std"] = df["value"].rolling(window=30, center=True, min_periods=15).std()
```

```python
phase_deg = (np.rad2deg(phase_rad) + 360.0) % 360.0
```

- 滑动窗口要按采样频率定义，不要对所有数据都写 30；日数据 30 d、月数据 12 month 的含义不同。
- 相位是循环量；`0°` 与 `360°` 等价，色标首尾要一致。

## 7. 常见数据错误

| 现象 | 根因 | 处理 |
|---|---|---|
| 图上下颠倒 | 纬度降序 / 深度正方向反了 | `sortby("lat")`；确认 depth 正负后再 `invert_yaxis` |
| 图左右断裂 | 经度 0–360 与 −180–180 混用 | 统一约定，跨日界线分段 |
| 区域裁剪为空 | 降序坐标 + `slice` | 先排序；打印数据范围 |
| 地图只有一条边 | `lon`/`lat` 与 `data` 形状 broadcast 错 | `validate_grid` |
| 色标全是一个颜色 | `vmin/vmax` 没覆盖数据，或全 NaN | 打印 `nanmin/nanmax/nanpercentile` |
| 陆地也被填色 | 没有 land mask / 没画陆地 | 用 `where` 掩膜或叠加 `cfeature.LAND` |
| 时间轴变成 1970 | 数值时间被当 datetime | 明确时间类型，别强转 |
| 关闭文件后数组失效 | 惰性 dask 数组 + `close()` | 先 `.load()` 或 `.compute()` |
