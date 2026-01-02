"""
Solvien Graph theme and style definitions - Altair (D3.js/Vega-Lite)
Professional, scientific and bioinformatics-focused design
"""

import altair as alt

SOLVIEN_THEMES = {
    "default": {
        "colors": ["#1f4788", "#2e75b6", "#4a90e2", "#6ba3e8", "#8db4ed"],
        "background": "#ffffff",
        "text": "#1a1a1a",
        "grid_color": "#e8e8e8",
        "accent": "#1f4788",
        "secondary": "#6c757d",
        "description": "Professional corporate theme (default)"
    },
    "scientific": {
        "colors": ["#2c3e50", "#34495e", "#7f8c8d", "#95a5a6", "#bdc3c7"],
        "background": "#ffffff",
        "text": "#2c3e50",
        "grid_color": "#ecf0f1",
        "accent": "#2c3e50",
        "secondary": "#7f8c8d",
        "description": "Theme optimized for scientific publications"
    },
    "publication": {
        "colors": ["#000000", "#333333", "#666666", "#999999", "#cccccc"],
        "background": "#ffffff",
        "text": "#000000",
        "grid_color": "#e0e0e0",
        "accent": "#000000",
        "secondary": "#666666",
        "description": "Black and white theme for high quality publications"
    },
    "bioinformatics": {
        "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"],
        "background": "#ffffff",
        "text": "#1a1a1a",
        "grid_color": "#f0f0f0",
        "accent": "#1f77b4",
        "secondary": "#7f7f7f",
        "description": "Color palette optimized for bioinformatics analyses"
    },
    "ibm": {
        "colors": ["#0f62fe", "#4589ff", "#78a9ff", "#a6c8ff", "#d0e2ff"],
        "background": "#ffffff",
        "text": "#161616",
        "grid_color": "#e0e0e0",
        "accent": "#0f62fe",
        "secondary": "#6c757d",
        "description": "Corporate blue color palette"
    },
    "google": {
        "colors": ["#4285F4", "#34A853", "#FBBC05", "#EA4335", "#9AA0A6"],
        "background": "#ffffff",
        "text": "#202124",
        "grid_color": "#dadce0",
        "accent": "#4285F4",
        "secondary": "#9AA0A6",
        "description": "Vibrant color palette"
    }
}

# Special color palettes for bioinformatics (Vega-Lite colormaps)
BIOINFORMATICS_PALETTES = {
    "viridis": "viridis",
    "plasma": "plasma",
    "inferno": "inferno",
    "magma": "magma",
    "cividis": "cividis",
    "coolwarm": "blueorange",
    "rdbu": "redblue"
}

DEFAULT_STYLE = {
    "width": 800,
    "height": 500,
    "font": "Arial, sans-serif",
    "title_fontsize": 20,
    "title_fontweight": "bold",
    "label_fontsize": 14,
    "label_fontweight": "normal",
    "tick_fontsize": 12,
    "legend_fontsize": 12,
    "padding": 20
}

PUBLICATION_STYLE = {
    "width": 800,
    "height": 600,
    "font": "Arial, sans-serif",
    "title_fontsize": 16,
    "title_fontweight": "bold",
    "label_fontsize": 12,
    "label_fontweight": "normal",
    "tick_fontsize": 10,
    "legend_fontsize": 12,
    "padding": 15
}


def get_theme(theme_name="default"):
    """Returns the specified theme. Default: professional corporate theme."""
    return SOLVIEN_THEMES.get(theme_name, SOLVIEN_THEMES["default"])


def get_bioinformatics_palette(palette_name="viridis"):
    """Returns color palette for bioinformatics."""
    return BIOINFORMATICS_PALETTES.get(palette_name, "viridis")


def configure_chart(chart, theme_name="default", publication_quality=False):
    """
    Applies professional style to Altair chart.
    """
    theme = get_theme(theme_name)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    config_dict = {
        'view': {
            'stroke': theme["grid_color"],
            'strokeWidth': 0.5,
            'fill': theme["background"]
        },
        'axis': {
            'domainColor': theme["grid_color"],
            'domainWidth': 1,
            'gridColor': theme["grid_color"],
            'gridOpacity': 0.15,
            'gridWidth': 0.5,
            'labelColor': theme["text"],
            'labelFont': style["font"],
            'labelFontSize': style["label_fontsize"],
            'labelFontWeight': style["label_fontweight"],
            'tickColor': theme["grid_color"],
            'tickSize': 5,
            'titleColor': theme["text"],
            'titleFont': style["font"],
            'titleFontSize': style["label_fontsize"],
            'titleFontWeight': style["label_fontweight"],
            'titlePadding': 10
        },
        'legend': {
            'labelColor': theme["text"],
            'labelFont': style["font"],
            'labelFontSize': style["legend_fontsize"],
            'titleColor': theme["text"],
            'titleFont': style["font"],
            'titleFontSize': style["label_fontsize"],
            'titleFontWeight': 'bold',
            'padding': 10,
            'strokeColor': theme["grid_color"],
            'strokeWidth': 1
        },
        'title': {
            'color': theme["text"],
            'font': style["font"],
            'fontSize': style["title_fontsize"],
            'fontWeight': style["title_fontweight"],
            'anchor': 'start',
            'offset': 20
        },
        'background': theme["background"]
    }
    
    return chart.configure(**config_dict)


def get_color_scheme(theme_name="default", n_colors=5):
    """Returns color scheme for theme."""
    theme = get_theme(theme_name)
    colors = theme["colors"][:n_colors]
    return colors
