"""
Solvien Graph - Professional data visualization library
Optimized for bioinformatics and scientific analyses, D3.js/Vega-Lite based interactive charts
Professional and beautiful visualizations using Altair
"""

from .core import (
    quick_bar,
    quick_line,
    quick_scatter,
    quick_pie,
    quick_hist
)
# Backward compatibility: import from bioinformatics.py
from .bioinformatics import (
    quick_heatmap,
    quick_volcano,
    quick_ma_plot,
    quick_violin,
    quick_boxplot
)
from .styles import (
    SOLVIEN_THEMES,
    BIOINFORMATICS_PALETTES,
    get_theme,
    get_bioinformatics_palette,
    configure_chart,
    DEFAULT_STYLE,
    PUBLICATION_STYLE
)

# Import biograph submodule
from . import biograph

__version__ = "0.3.0"
__author__ = "Yasin Polat"

__all__ = [
    # Basic charts
    "quick_bar",
    "quick_line",
    "quick_scatter",
    "quick_pie",
    "quick_hist",
    # Bioinformatics charts (backward compatibility)
    "quick_heatmap",
    "quick_volcano",
    "quick_ma_plot",
    "quick_violin",
    "quick_boxplot",
    # Biograph submodule
    "biograph",
    # Theme and style
    "SOLVIEN_THEMES",
    "BIOINFORMATICS_PALETTES",
    "get_theme",
    "get_bioinformatics_palette",
    "configure_chart",
    "DEFAULT_STYLE",
    "PUBLICATION_STYLE",
]