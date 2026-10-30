# 海洋学绘图教程

> **给 AI 的说明：** 本目录是给人看的教学材料。除非用户明确要求“讲解 / 教学 / 入门 / 写教程”，不要读取本目录，不要因为这里的内容而扩大绘图任务。机器绘图请使用 `references/figure-catalog.md`、`references/recipes/` 和 `templates/`。

本目录面向刚开始做海洋学绘图的读者，目标是解释**为什么**这样做，而不只是给代码。机器配方已经是可执行版本；教程负责数据格式、投影选择、图层语义和常见错误。

## 作者说明

这些教程由作者本人后续亲自补足，尽量不使用 AI 辅助创作。教程会尽量公开作者论文中的研究问题、数据与统计设计、分析方法和绘图决策，而不只是贴出最终代码或结果图；重点是让读者理解“为什么这样做”，以及哪些假设和边界需要自己检查。AI 在仓库中只用于结构、链接和构建检查，不代写教程正文。

## 学习路线

1. **安装与环境**
   - Python、conda、Cartopy、cmocean、xarray
   - 为什么 Cartopy 在 Windows 上更适合 conda
   - 如何验证安装

2. **NetCDF、变量与坐标**
   - 维度、坐标、数据变量
   - CF `standard_name`、units、`positive`
   - `valid_time`、`time_counter`、`nav_lon`、`uos/vos`
   - 用 `ocean-plot --inspect` 先诊断

3. **投影怎么选**
   - 区域中低纬：Mercator
   - 全球：Robinson / EqualEarth
   - 极地：PolarStereo
   - 高纬区域：LambertConformal
   - 数据 transform 始终是 PlateCarree
   - 非矩形投影的 gridline 标签

4. **常见图型**
   - 地形、SST、SSS、SSH
   - 流场、海冰、叶绿素、MLD
   - 垂向剖面、Hovmöller、T-S
   - 多面板与共享 colorbar

5. **统计分析**
   - 时间序列、距平、趋势
   - FFT、小波、EOF/PCA、CCA、EMD
   - 显著性、零假设和边界条件
   - Taylor/Target 图

6. **物理海洋学专题**
   - 水团、锋面、涡旋
   - 输运、EKE、能量转换
   - 混合层与上层海洋
   - 海冰季节循环与趋势

## 机器入口

- 图型目录：`references/figure-catalog.md`
- 配方索引：`references/recipes/README.md`
- 数据与命名诊断：`references/netcdf-profiles.md`
- 可运行模板：`templates/`

教程中的代码应链接到配方或模板，不另维护一套容易过时的实现。

## 状态

目前是教程索引和结构骨架；具体教程在后续迭代中逐步补齐。未完成的页面不会以“已实现”名义出现在图型目录中。
