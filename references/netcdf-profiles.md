# NetCDF 命名与诊断

目标不是猜对所有文件，而是让代码在进入绘图前**明确知道**变量、坐标、时间和垂直方向；不能确定时报告候选，而不是静默选第一个。

运行时代码在 [`scripts/ocean_vocab.py`](../scripts/ocean_vocab.py)。

## 1. 先诊断，不要先画

```bash
ocean-plot --inspect data.nc
ocean-plot --inspect data.nc > report.json
```

Python：

```python
import xarray as xr
from ocean_vocab import inspect_dataset, resolve_variable

with xr.open_dataset("data.nc", decode_times=True, mask_and_scale=True) as ds:
    report = inspect_dataset(ds, path="data.nc")
    print(report.as_dict())
    name = resolve_variable(ds, "sst")
```

报告包含：

- 实际使用的 `lon/lat/time/depth` 坐标名和维度；
- 时间 dtype、calendar、units；
- 已识别语义变量及其候选；
- 2D 曲线坐标、投影坐标、sigma 垂直坐标等警告。

## 2. 解析优先级

1. CF `standard_name`；
2. units / `positive` 等属性；
3. 通用变量别名；
4. 产品 profile（ERA5、GLORYS、NEMO、ROMS、CMIP6）；
5. 用户显式指定变量名或语义 key。

如果多个候选同时匹配，`resolve_variable()` 抛 `ValueError`，列出候选并要求更具体的 `key`。

## 3. 常见命名

| 语义 | 常见名称 | 备注 |
|---|---|---|
| 时间 | `time`, `valid_time`, `time_counter`, `ocean_time` | `forecast_reference_time` 不是预报有效时间 |
| 经度 | `lon`, `longitude`, `nav_lon`, `lon_rho`, `TLONG` | 2D 坐标保留原生布局 |
| 纬度 | `lat`, `latitude`, `nav_lat`, `lat_rho`, `TLAT` | 同上 |
| 深度 | `depth`, `deptht`, `st_ocean`, `lev` | `s_rho`/`siglay` 是 sigma 坐标，不能直接当米 |
| 海表高度 | `ssh`, `zos`, `sla`, `adt` | 注意基准面/动力地形差异 |
| 表层流 | `uos`, `vos`, `water_u`, `water_v` | 与 3D `uo/vo` 分开 |
| 风 | `u10`, `v10`, `10u`, `10v` | 与海流分开 |
| 温度 | `thetao`, `temp`, `sea_water_temperature` | `sst/tos` 是表层温度 |
| 盐度 | `so`, `salt`, `sea_water_salinity` | `sss/sos` 是表层盐度 |
| 海冰 | `siconc`, `sithick`, `usi`, `vsi` | 浓度单位可能是 0–1 或 % |
| 地形 | `deptho`, `bathymetry`, `topo` | 注意正向下/高程符号 |

## 4. 产品 profile

`ocean_vocab.PRODUCT_PROFILES` 目前提供：

- `era5`
- `glorys`
- `nemo`
- `roms`
- `cmip6`

profile 只是别名提示，不替代实际检查。新增 profile 时应：

1. 先加一个最小合成数据集测试；
2. 在 `inspect_dataset()` 报告里能看到候选；
3. 不改变已有通用匹配规则；
4. 文件/变量名不确定时保持 `planned`，不要声称支持。

## 5. 常见边界

- **时间**：先确认 `valid_time`、`time_counter` 等含义；不要把 `forecast_reference_time` 当时间轴。
- **2D 坐标**：`nav_lon/nav_lat` 支持读取，但不排序、不 unwrap；跨日界线保留原生布局。
- **sigma 坐标**：`s_rho`/`siglay` 需要层厚/压力转换，不能当 `depth`。
- **单位**：`sithick` 可能是 m、`siconc` 可能是 %；图上必须标清。
- **多文件/组**：先确认 `open_mfdataset` 的 combine 维和 group，再进入绘图。
- **投影坐标**：`x/y` 单位是 m/km 时不要改名成 lon/lat；使用原生投影。

## 6. 人类教程

变量和坐标的入门解释见 [`docs/tutorials/README.md`](../docs/tutorials/README.md)；AI 在普通绘图任务中默认不读取该教程。
