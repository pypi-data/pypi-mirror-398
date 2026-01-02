import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import AutoMinorLocator, MaxNLocator
from matplotlib.axes._axes import Axes


class cm_to_inch:
    def __call__(self, cm: float) -> float:
        """厘米转英寸"""
        return cm / 2.54

    def __mul__(self, other: float) -> float:
        """实例作为左操作数时，实现 x * 数值 的乘法运算（厘米转英寸）"""
        return other / 2.54

    def __rmul__(self, other: float) -> float:
        """实例作为右操作数时，实现 数值 * x 的乘法运算（厘米转英寸）"""
        return self.__mul__(other)


cm = cm_to_inch()


def whole_plot_set(
    font=["Times New Roman", "SimSun"],
    math_font="stix",  # 公式使用STIX字体，接近Times风格。这里不设置Times New Roman字体是因为Matplotlib不支持
) -> None:
    """设置全局绘图参数"""
    # 设置线宽
    plt.rcParams["lines.linewidth"] = 1
    plt.rcParams["font.family"] = ", ".join(font)
    plt.rcParams["font.family"] = "Times new roman, SimSun"  # 设置字体为Times New Roman
    plt.rcParams["font.serif"] = ["Times New Roman", "SimSun"]
    plt.rcParams["mathtext.fontset"] = math_font
    plt.rcParams["xtick.direction"] = "in"  # 设置x刻度线朝内
    plt.rcParams["ytick.direction"] = "in"  # 设置y刻度线朝内
    plt.rcParams["legend.fancybox"] = False  # 设置图例无圆角
    plt.rcParams["figure.dpi"] = 300


def set_ticks(
    ax: Axes,
    xrange: tuple = None,
    yrange: tuple = None,
    majorMaxNLocator: int = None,
    minorLocator: int = 2,
    have_x_major: bool = True,
    have_y_major: bool = True,
    have_x_label: bool = True,
    have_y_label: bool = True,
):
    """
    设置坐标轴范围和刻度
    :param ax: 坐标轴对象
    :param xrange: x轴范围和间距, 格式为(xmin, xmax, xsep)
    :param yrange: y轴范围和间距, 格式为(ymin, ymax, ysep)
    :param majorMaxNLocator: 主刻度最大数量
    :param minorLocator: 每两个主刻度之间的次刻度数量(默认为2)
    :param have_x_major: 是否显示x轴主刻度
    :param have_y_major: 是否显示y轴主刻度
    :param have_x_label: 是否显示x轴刻度值
    :param have_y_label: 是否显示y轴刻度值
    :return:
    """
    if xrange is not None:
        xmin, xmax, xsep = xrange
        ax.set_xlim(xmin, xmax)
        ax.set_xticks(
            np.arange(xmin, xmax + xsep / 10, xsep),
        )
    if yrange is not None:
        ymin, ymax, ysep = yrange
        ax.set_ylim(ymin, ymax)
        ax.set_yticks(
            np.arange(ymin, ymax + ysep / 10, ysep),
        )
    # 设置坐标轴刻度
    if majorMaxNLocator is not None:
        ax.xaxis.set_major_locator(MaxNLocator(majorMaxNLocator))
        ax.yaxis.set_major_locator(MaxNLocator(majorMaxNLocator))
    if minorLocator is not None:
        ax.xaxis.set_minor_locator(AutoMinorLocator(minorLocator))
        ax.yaxis.set_minor_locator(AutoMinorLocator(minorLocator))

    ax.tick_params(
        axis="x",
        which="major" if have_x_major else "both",
        bottom=have_x_major,
        labelbottom=have_x_label,
    )
    ax.tick_params(
        axis="y",
        which="major" if have_y_major else "both",
        left=have_y_major,
        labelleft=have_y_label,
    )


def half_plot_set(ax) -> None:
    plt.rcParams["lines.linewidth"] = 0.5

    ax_linewidth = 0.5

    ax.spines["top"].set_linewidth(ax_linewidth)
    ax.spines["right"].set_linewidth(ax_linewidth)
    ax.spines["left"].set_linewidth(ax_linewidth)
    ax.spines["bottom"].set_linewidth(ax_linewidth)

    # 设置刻度线宽为0.5
    ax_tick_linewidth = 0.3
    ax.tick_params(axis="both", which="major", width=ax_tick_linewidth)
    ax.tick_params(axis="both", which="minor", width=ax_tick_linewidth)

    # 设置刻度长度
    ax.tick_params(axis="both", which="major", length=2)
    ax.tick_params(axis="both", which="minor", length=1)

    # 设置刻度字体大小为6
    ax.tick_params(axis="both", which="major", labelsize=6)
