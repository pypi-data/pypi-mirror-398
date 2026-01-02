"""
PltSci - A utility library for matplotlib plotting configuration

This package provides utilities for simplified matplotlib plot configuration.
"""

from .function import (
    cm_to_inch,
    cm,
    whole_plot_set,
    set_ticks,
    half_plot_set
)

__version__ = "0.1.0"
__author__ = "Muxkin"

__all__ = [
    "cm_to_inch",
    "cm", 
    "whole_plot_set",
    "set_ticks",
    "half_plot_set"
]
