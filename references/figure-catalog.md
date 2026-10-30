# 图型目录

这是机器和人的共同入口。AI 绘图时先在这里选 `key`，再进入对应 recipe；不要先扫全部 reference 文件。

状态说明：

- `implemented`：配方存在且已接入现有测试；
- `planned`：目录先占位，尚未实现，不能拿来声称已支持；
- `recipe` 是机器配方，`tutorial` 是给人看的教学页（可留空）。

## 已实现

| key | 图型 | 必需语义变量 | 推荐投影 | 机器 recipe | 人类 tutorial | 状态 |
|---|---|---|---|---|---|---|
| `map.regional` | 单张区域地图 | `lon`, `lat`, 目标场 | 区域 Mercator | [maps.md](recipes/maps.md#1-单张区域地图) | — | implemented |
| `map.multipanel` | 多面板地图共用色标 | `lon`, `lat`, 目标场（可多帧） | 区域 Mercator | [maps.md](recipes/maps.md#2-多面板地图共用色标) | — | implemented |
| `map.phase` | 相位图 | `lon`, `lat`, `phase_rad` | 区域 Mercator | [maps.md](recipes/maps.md#3-相位) | — | implemented |
| `map.bathymetry` | 水深/地形 | `lon`, `lat`, `bathymetry` | 区域 Mercator；极地 PolarStereo | [maps.md](recipes/maps.md#4-地形--陆架坡折) | — | implemented |
| `section.hovmoller` | Hovmöller | `distance/time` 或 `lat/time` 场 | 无地图 | [sections.md](recipes/sections.md#1-hovmöller-图) | — | implemented |
| `section.vertical` | 垂向剖面 | `time/depth` 或 `distance/depth` 场 | 无地图 | [sections.md](recipes/sections.md#2-垂向剖面) | — | implemented |
| `time.series` | 时间序列 + 标准差 | `dates`, `mean`, `std` | 无地图 | [time-series.md](recipes/time-series.md#1-时间序列--标准差) | — | implemented |
| `stats.scatter` | 散点/属性图 | `x`, `y`, `values` | 无地图 | [statistics.md](recipes/statistics.md#1-散点--属性图) | — | implemented |
| `spectral.fft` | FFT 振幅谱 | 1D 规则序列 | 无地图 | [spectral.md](recipes/spectral.md#1-fft-频谱) | — | implemented |
| `flow.quiver` | 流场/力场箭头 | `lon`, `lat`, `u_current`, `v_current` | 区域 Mercator | [flow.md](recipes/flow.md#1-quiver流场力场) | — | implemented |
| `flow.trajectories` | 粒子轨迹/LineCollection | `trajectories`, `values` | 区域 Mercator | [flow.md](recipes/flow.md#2-粒子轨迹--linecollection) | — | implemented |

## 计划中

这些是结构占位，不代表已实现。实现时必须同时补 recipe、catalog、相关测试和 CHANGELOG。

| key | 图型 | 必需语义变量 | 推荐投影 | 机器 recipe | 人类 tutorial | 状态 |
|---|---|---|---|---|---|---|
| `map.sst` | 海表温度 | `sst` | 区域 Mercator | — | — | planned |
| `map.sss` | 海表盐度 | `sss` | 区域 Mercator | — | — | planned |
| `map.ssh` | 海面高度/动力地形 | `ssh` | 区域 Mercator；全球 Robinson | — | — | planned |
| `map.currents` | 表层流场 | `u_surface`, `v_surface` | 区域 Mercator | — | — | planned |
| `map.ice_concentration` | 海冰覆盖 | `ice_concentration` | 极地 PolarStereo | — | — | planned |
| `map.ice_thickness` | 海冰厚度 | `ice_thickness` | 极地 PolarStereo | — | — | planned |
| `map.chlorophyll` | 叶绿素 | `chlorophyll` | 区域 Mercator | — | — | planned |
| `map.mld` | 混合层深度 | `mld` | 区域 Mercator | — | — | planned |
| `section.ts` | 温盐断面 | `temp`, `salt`, `depth` | 无地图 | — | — | planned |
| `stats.eof` | EOF/PCA | 时空场 | 无地图 | — | — | planned |
| `stats.wavelet` | 小波 | 1D 规则序列 | 无地图 | — | — | planned |
| `stats.cca` | CCA | 两组时空场 | 无地图 | — | — | planned |
| `stats.emd` | EMD | 1D 序列 | 无地图 | — | — | planned |
| `stats.taylor` | Taylor 图 | 模型/观测统计量 | 无地图 | — | — | planned |
| `ice.seasonal` | 海冰季节循环 | `ice_concentration` | 无地图 | — | — | planned |
| `ice.trend` | 海冰趋势 | `ice_concentration` | 极地 PolarStereo | — | — | planned |

## 新增图型的 Definition of Done

1. 在 catalog 中新增/更新一行，写清语义变量、投影和状态。
2. 在 `references/recipes/` 对应领域新增配方，含数据契约、import 和验收。
3. 需要通用计算时，才改 `scripts/`；一次性图型不要污染核心 API。
4. 需要完整 demo 时，才加 `templates/`；不要每个图型都复制一个模板。
5. 跑 `python -m pytest -q`，至少覆盖 catalog/recipe 链接；新增 helper 时补单元测试。
6. 用户可见变化写入 `CHANGELOG.md`；版本和 release 等明确要求再做。

## 相关入口

- 通用参数与配方索引：[recipes/README.md](recipes/README.md)
- 数据准备与变量识别：[data-prep.md](data-prep.md)
- NetCDF 命名与诊断：[netcdf-profiles.md](netcdf-profiles.md)
- 投影与风格：[style-reference.md](style-reference.md)
- 人类教程：[../docs/tutorials/README.md](../docs/tutorials/README.md)
