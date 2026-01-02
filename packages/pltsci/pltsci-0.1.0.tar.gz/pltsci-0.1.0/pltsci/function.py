import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import AutoMinorLocator
from matplotlib.axes._axes import Axes

class cm_to_inch:
    @staticmethod
    def __call__(cm: float) -> float:
        """厘米转英寸"""
        return cm / 2.54
    
    @staticmethod
    def __mul__(cm: float) -> float:
        """厘米转英寸"""
        return cm / 2.54

cm = cm_to_inch()

def whole_plot_set(
    font = ["Times New Roman","SimSun"], 
    math_font = "stix" # 公式使用STIX字体，接近Times风格。这里不设置Times New Roman字体是因为Matplotlib不支持
    ) -> None:
    """设置全局绘图参数"""
    # 设置线宽
    plt.rcParams["lines.linewidth"] = 1
    plt.rcParams["font.family"] = ", ".join(font)
    plt.rcParams["font.family"] = "Times new roman, SimSun"  # 设置字体为Times New Roman
    plt.rcParams["font.serif"] = ["Times New Roman","SimSun"]
    plt.rcParams["mathtext.fontset"] = (math_font  )
    plt.rcParams["xtick.direction"] = "in"  # 设置x刻度线朝内
    plt.rcParams["ytick.direction"] = "in"  # 设置y刻度线朝内
    plt.rcParams["legend.fancybox"] = False  # 设置图例无圆角





def set_ticks(ax: Axes, xrange: tuple = None, yrange: tuple = None):
    """
    设置坐标轴范围和刻度
    :param ax: 坐标轴对象
    :param xrange: x轴范围和间距, 格式为(xmin, xmax, xsep)
    :param yrange: y轴范围和间距, 格式为(ymin, ymax, ysep)
    :return:
    """
    if xrange is not None:
        xmin, xmax, xsep = xrange
        ax.set_xlim(xmin, xmax)
        # 设置x轴、y轴间距
        # ax.xticks()
        ax.set_xticks(
            np.arange(xmin, xmax + xsep / 10, xsep),
            #   minor=True
        )
    if yrange is not None:
        ymin, ymax, ysep = yrange
        ax.set_ylim(ymin, ymax)
        ax.set_yticks(
            np.arange(ymin, ymax + ysep / 10, ysep),
            #   minor=True
        )
    # 设置坐标轴刻度
    # ax.xaxis.set_major_locator(MaxNLocator(5))  # 主刻度数量
    # ax.yaxis.set_major_locator(MaxNLocator(5))  # 主刻度数量
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))  # 参数n=2表示主刻度之间分成2份（即1个小刻度）
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))  # 参数n=2表示主刻度之间分成2份（即1个小刻度）


def half_plot_set(ax) -> None:
    # 设置坐标轴线宽为0.5
    # 设置坐标轴线宽为0.5
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
    ax.tick_params(axis="both", which="minor", length=1.3)

    # 设置刻度字体大小为6
    ax.tick_params(axis="both", which="major", labelsize=6)
