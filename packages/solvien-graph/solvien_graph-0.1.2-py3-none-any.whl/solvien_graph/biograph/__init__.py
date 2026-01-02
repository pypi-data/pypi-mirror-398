"""
Solvien Graph - Biograph Module
Specialized bioinformatics visualization toolkit
Interactive D3.js/Vega-Lite based charts for genomic and gene expression data
"""

from .charts import (
    quick_heatmap,
    quick_volcano,
    quick_ma_plot,
    quick_violin,
    quick_boxplot
)

__version__ = "0.1.0"
__author__ = "Yasin Polat"

__all__ = [
    "quick_heatmap",
    "quick_volcano",
    "quick_ma_plot",
    "quick_violin",
    "quick_boxplot",
]
