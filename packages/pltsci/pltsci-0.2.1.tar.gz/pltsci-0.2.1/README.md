# PltSci

一个用于简化 matplotlib 绘图参数设置的 Python 工具库。

## 安装

```bash
pip install pltsci
```

## 快速开始

**示例：创建一个全宽的科学绘图**

```python
from pltsci import whole_plot_set, set_ticks, cm
import matplotlib.pyplot as plt
import numpy as np

# 设置全局绘图参数
whole_plot_set()  # 全宽图片参数设置
fig, ax = plt.subplots(figsize=(15 * cm, 10 * cm), dpi=300)  # 创建图形 (使用厘米单位)

# 创建示例数据
x = np.linspace(0, 10, 100)
y = np.sin(x)

ax.plot(x, y, label="$y=\\sin(x)$")

# 设置坐标轴范围和刻度
set_ticks(ax, xrange=(0, 10, 2), yrange=(-1.5, 1.5, 0.5))

# 添加标签和图例
ax.set_xlabel("x", fontsize=12)
ax.set_ylabel("y", fontsize=12)
ax.legend()

plt.tight_layout()
fig.savefig("examples/whole_plot.svg", bbox_inches="tight")
```

结果：

![whole_plot_example](examples/whole_plot.svg)

**示例：创建一个半宽的科学绘图**

```python
from pltsci import whole_plot_set, half_plot_set, set_ticks, cm
import matplotlib.pyplot as plt
import numpy as np

# 设置全局绘图参数
whole_plot_set()  # 全宽图片参数设置，即使是用半宽图，也建议先调用此函数设置全局参数
fig, ax = plt.subplots(figsize=(7 * cm, 5 * cm), dpi=300)  # 创建图形 (使用厘米单位)
half_plot_set(ax)  # 半宽图片参数设置

# 创建示例数据
x = np.linspace(0, 10, 100)
y = np.exp(x)

ax.plot(x, y, label="$y=e^x$")

# 设置坐标轴范围和刻度
set_ticks(ax, xrange=(0, 10, 2), yrange=(0, 22000, 5000))

# 添加标签和图例
ax.set_xlabel("x", fontsize=10)
ax.set_ylabel("y", fontsize=10)
ax.legend(fontsize=8)

plt.tight_layout()
fig.savefig("examples/half_plot.svg", bbox_inches="tight")
# fig.savefig("examples/half_plot.jpg", bbox_inches="tight", dpi=1200) # 位图记得设置高分辨率
```

结果：

![half_plot_example](examples/half_plot.svg)

## API 参考

### `whole_plot_set(font=None, math_font="stix")`

设置全局绘图参数，包括字体、刻度方向、图例样式等。

- `font`: 字体列表，默认为 `["Times New Roman", "SimSun"]`
- `math_font`: 数学公式字体，默认为 `"stix"`

### `set_ticks(ax, xrange=None, yrange=None)`

设置坐标轴范围和刻度。

- `ax`: matplotlib 轴对象
- `xrange`: x轴范围，格式为 `(xmin, xmax, xstep)`
- `yrange`: y轴范围，格式为 `(ymin, ymax, ystep)`
- `majorMaxNLocator`: 主刻度最大数量，默认为None
- `minorLocator`: 每两个主刻度之间的次刻度数量，默认为 2
- `have_x_major`: 是否显示 x 轴主刻度，默认为 True
- `have_y_major`: 是否显示 y 轴主刻度，默认为 True
- `have_x_label`: 是否显示 x 轴刻度值，默认为 True
- `have_y_label`: 是否显示 y 轴刻度值，默认为 True

### `half_plot_set(ax)`

设置坐标轴线宽和刻度样式，适用于密集布局的图表。

- `ax`: matplotlib 轴对象

### `cm`

厘米到英寸转换工具。

```python
# 两种使用方式
fig, ax = plt.subplots(figsize=(15 * cm, 10 * cm))
# 或者
fig, ax = plt.subplots(figsize=(cm(15), cm(10)))
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！
