"""
Solvien Graph - Professional Chart Styling System
Enterprise-grade, minimalist design system for data visualization
"""

import altair as alt

# =============================================================================
# PROFESSIONAL FONT STACKS - MODERN & CLEAN
# =============================================================================
# Modern sans-serif (Inter is the go-to modern font)
MODERN_FONT_STACK = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
# Corporate/Enterprise (clean and professional)
CORPORATE_FONT_STACK = "Inter, SF Pro Display, Helvetica Neue, Arial, sans-serif"
# Scientific/Publication (modern but professional - no more Times New Roman!)
PUBLICATION_FONT_STACK = "Inter, Roboto, Source Sans Pro, Helvetica Neue, sans-serif"

# =============================================================================
# PROFESSIONAL COLOR PALETTES
# =============================================================================
CORPORATE_COLORS = {
    # Primary Blues
    "blue": ["#001141", "#002d9c", "#0043ce", "#0f62fe", "#4589ff", "#78a9ff", "#a6c8ff", "#d0e2ff", "#edf5ff"],
    # Grays (Cool Gray)
    "gray": ["#121619", "#21272a", "#343a3f", "#4d5358", "#697077", "#878d96", "#a2a9b0", "#c1c7cd", "#dde1e6", "#f2f4f8"],
    # Support colors
    "green": ["#044317", "#0e6027", "#198038", "#24a148", "#42be65", "#6fdc8c", "#a7f0ba", "#defbe6"],
    "red": ["#2d0709", "#520408", "#750e13", "#a2191f", "#da1e28", "#fa4d56", "#ff8389", "#ffb3b8", "#ffd7d9"],
    "purple": ["#1c0f30", "#31135e", "#491d8b", "#6929c4", "#8a3ffc", "#a56eff", "#be95ff", "#d4bbff", "#e8daff"],
    "cyan": ["#061727", "#012749", "#003a6d", "#00539a", "#0072c3", "#1192e8", "#33b1ff", "#82cfff", "#bae6ff"],
    "teal": ["#081a1c", "#022b30", "#004144", "#005d5d", "#007d79", "#009d9a", "#08bdba", "#3ddbd9", "#9ef0f0"],
    "magenta": ["#2a0a18", "#510224", "#740937", "#9f1853", "#d02670", "#ee5396", "#ff7eb6", "#ffafd2", "#ffd6e8"],
    "orange": ["#231000", "#3e1a00", "#5e2900", "#8a3800", "#ba4e00", "#eb6200", "#ff832b", "#ffb784", "#ffd9be"],
}

# =============================================================================
# THEME DEFINITIONS
# =============================================================================
SOLVIEN_THEMES = {
    # --- CORPORATE / ENTERPRISE ---
    "corporate": {
        "colors": ["#0f62fe", "#4589ff", "#78a9ff", "#a6c8ff", "#d0e2ff"],
        "sequential": CORPORATE_COLORS["blue"],
        "categorical": ["#0f62fe", "#24a148", "#8a3ffc", "#1192e8", "#ee5396", "#6929c4"],
        "background": "#ffffff",
        "text": "#161616",
        "text_secondary": "#525252",
        "grid_color": "#e0e0e0",
        "grid_opacity": 0.4,
        "accent": "#0f62fe",
        "secondary": "#6f6f6f",
        "font": CORPORATE_FONT_STACK,
        "description": "Professional corporate design"
    },
    "corporate_dark": {
        "colors": ["#78a9ff", "#4589ff", "#0f62fe", "#002d9c", "#001141"],
        "sequential": list(reversed(CORPORATE_COLORS["blue"])),
        "categorical": ["#78a9ff", "#42be65", "#be95ff", "#33b1ff", "#ff7eb6", "#a56eff"],
        "background": "#161616",
        "text": "#f4f4f4",
        "text_secondary": "#c6c6c6",
        "grid_color": "#393939",
        "grid_opacity": 0.5,
        "accent": "#78a9ff",
        "secondary": "#8d8d8d",
        "font": CORPORATE_FONT_STACK,
        "description": "Corporate design - Dark Mode"
    },
    # --- MODERN / VIBRANT ---
    "modern": {
        "colors": ["#4285F4", "#34A853", "#FBBC05", "#EA4335", "#9AA0A6"],
        "sequential": ["#E8F0FE", "#D2E3FC", "#A8C7FA", "#7BAAF7", "#4285F4", "#1967D2", "#185ABC", "#1A73E8"],
        "categorical": ["#4285F4", "#34A853", "#FBBC05", "#EA4335", "#673AB7", "#00BCD4"],
        "background": "#ffffff",
        "text": "#202124",
        "text_secondary": "#5f6368",
        "grid_color": "#dadce0",
        "grid_opacity": 0.5,
        "accent": "#4285F4",
        "secondary": "#9AA0A6",
        "font": MODERN_FONT_STACK,
        "description": "Modern vibrant design"
    },
    "modern_dark": {
        "colors": ["#8AB4F8", "#81C995", "#FDD663", "#F28B82", "#AECBFA"],
        "sequential": ["#174EA6", "#1967D2", "#1A73E8", "#4285F4", "#669DF6", "#8AB4F8", "#AECBFA", "#D2E3FC"],
        "categorical": ["#8AB4F8", "#81C995", "#FDD663", "#F28B82", "#C58AF9", "#78D9EC"],
        "background": "#202124",
        "text": "#E8EAED",
        "text_secondary": "#9AA0A6",
        "grid_color": "#3c4043",
        "grid_opacity": 0.5,
        "accent": "#8AB4F8",
        "secondary": "#9AA0A6",
        "font": MODERN_FONT_STACK,
        "description": "Modern design - Dark Mode"
    },
    # --- MINIMALIST / CLEAN ---
    "minimal": {
        "colors": ["#1a1a1a", "#4a4a4a", "#7a7a7a", "#aaaaaa", "#dadada"],
        "sequential": ["#f7f7f7", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525"],
        "categorical": ["#1a1a1a", "#e63946", "#2a9d8f", "#457b9d", "#f4a261", "#6c757d"],
        "background": "#ffffff",
        "text": "#1a1a1a",
        "text_secondary": "#6c757d",
        "grid_color": "#f0f0f0",
        "grid_opacity": 0.8,
        "accent": "#1a1a1a",
        "secondary": "#6c757d",
        "font": MODERN_FONT_STACK,
        "description": "Clean minimalist design"
    },
    # --- PUBLICATION / SCIENTIFIC ---
    "publication": {
        "colors": ["#000000", "#252525", "#525252", "#737373", "#969696", "#bdbdbd", "#d9d9d9"],
        "sequential": ["#f7f7f7", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525", "#000000"],
        "categorical": ["#000000", "#525252", "#969696", "#bdbdbd", "#d9d9d9", "#f0f0f0"],
        "background": "#ffffff",
        "text": "#000000",
        "text_secondary": "#525252",
        "grid_color": "#e5e5e5",
        "grid_opacity": 0.6,
        "accent": "#000000",
        "secondary": "#525252",
        "font": PUBLICATION_FONT_STACK,
        "description": "Publication-ready grayscale"
    },
    # --- SCIENTIFIC / BIOINFORMATICS ---
    "scientific": {
        "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"],
        "sequential": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"],
        "categorical": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"],
        "background": "#ffffff",
        "text": "#2c3e50",
        "text_secondary": "#7f8c8d",
        "grid_color": "#ecf0f1",
        "grid_opacity": 0.5,
        "accent": "#1f77b4",
        "secondary": "#7f8c8d",
        "font": MODERN_FONT_STACK,
        "description": "Scientific visualization palette"
    },
    # --- DEFAULT (Corporate style) ---
    "default": {
        "colors": ["#0f62fe", "#4589ff", "#78a9ff", "#a6c8ff", "#d0e2ff"],
        "sequential": ["#edf5ff", "#d0e2ff", "#a6c8ff", "#78a9ff", "#4589ff", "#0f62fe", "#0043ce", "#002d9c"],
        "categorical": ["#0f62fe", "#24a148", "#8a3ffc", "#1192e8", "#ee5396", "#6929c4"],
        "background": "#ffffff",
        "text": "#161616",
        "text_secondary": "#525252",
        "grid_color": "#e0e0e0",
        "grid_opacity": 0.4,
        "accent": "#0f62fe",
        "secondary": "#6c757d",
        "font": MODERN_FONT_STACK,
        "description": "Professional corporate theme (default)"
    },
}

# =============================================================================
# BIOINFORMATICS COLOR PALETTES (Vega-Lite colormaps)
# =============================================================================
BIOINFORMATICS_PALETTES = {
    "viridis": "viridis",
    "plasma": "plasma",
    "inferno": "inferno",
    "magma": "magma",
    "cividis": "cividis",
    "coolwarm": "blueorange",
    "rdbu": "redblue",
    "turbo": "turbo",
    "spectral": "spectral",
}

# =============================================================================
# STYLE PRESETS
# =============================================================================
# Corporate/Enterprise typography scale
CORPORATE_STYLE = {
    "width": 640,
    "height": 400,
    "font": CORPORATE_FONT_STACK,
    "title_fontsize": 20,
    "title_fontweight": 600,
    "label_fontsize": 14,
    "label_fontweight": 400,
    "tick_fontsize": 12,
    "legend_fontsize": 12,
    "legend_title_fontsize": 12,
    "padding": 24,
    "title_line_height": 1.25,
    "corner_radius": 0,  # Sharp corners for professional look
    "stroke_width": 1.5,
}

# Modern clean style
MODERN_STYLE = {
    "width": 640,
    "height": 400,
    "font": MODERN_FONT_STACK,
    "title_fontsize": 18,
    "title_fontweight": 500,
    "label_fontsize": 12,
    "label_fontweight": 400,
    "tick_fontsize": 11,
    "legend_fontsize": 11,
    "legend_title_fontsize": 12,
    "padding": 20,
    "title_line_height": 1.4,
    "corner_radius": 4,  # Subtle rounding
    "stroke_width": 2,
}

# Clean minimal style
MINIMAL_STYLE = {
    "width": 640,
    "height": 400,
    "font": MODERN_FONT_STACK,
    "title_fontsize": 16,
    "title_fontweight": 600,
    "label_fontsize": 12,
    "label_fontweight": 400,
    "tick_fontsize": 11,
    "legend_fontsize": 11,
    "legend_title_fontsize": 11,
    "padding": 16,
    "title_line_height": 1.3,
    "corner_radius": 2,
    "stroke_width": 1.5,
}

# Publication quality (journals, papers)
PUBLICATION_STYLE = {
    "width": 600,
    "height": 400,
    "font": PUBLICATION_FONT_STACK,
    "title_fontsize": 14,
    "title_fontweight": "bold",
    "label_fontsize": 12,
    "label_fontweight": "normal",
    "tick_fontsize": 10,
    "legend_fontsize": 10,
    "legend_title_fontsize": 11,
    "padding": 12,
    "title_line_height": 1.2,
    "corner_radius": 0,
    "stroke_width": 1,
}

# Default style (uses corporate clean look)
DEFAULT_STYLE = CORPORATE_STYLE.copy()


def get_style_for_theme(theme_name="default"):
    """Returns the appropriate style preset for a theme."""
    if theme_name in ["corporate", "corporate_dark"]:
        return CORPORATE_STYLE
    elif theme_name in ["modern", "modern_dark"]:
        return MODERN_STYLE
    elif theme_name == "minimal":
        return MINIMAL_STYLE
    elif theme_name == "publication":
        return PUBLICATION_STYLE
    return DEFAULT_STYLE


def get_theme(theme_name="default"):
    """Returns the specified theme. Default: professional corporate theme."""
    return SOLVIEN_THEMES.get(theme_name, SOLVIEN_THEMES["default"])


def get_bioinformatics_palette(palette_name="viridis"):
    """Returns color palette for bioinformatics."""
    return BIOINFORMATICS_PALETTES.get(palette_name, "viridis")


def configure_chart(chart, theme_name="default", publication_quality=False):
    """
    Applies professional enterprise-grade style to Altair chart.
    Clean, minimal, data-focused design.
    """
    theme = get_theme(theme_name)
    
    if publication_quality:
        style = PUBLICATION_STYLE
    else:
        style = get_style_for_theme(theme_name)
    
    # Build configuration
    config_dict = {
        # View configuration
        'view': {
            'stroke': None,  # No border around chart area
            'strokeWidth': 0,
            'fill': None,  # Transparent view background
            'continuousWidth': style["width"],
            'continuousHeight': style["height"],
        },
        # Axis configuration - minimal, clean
        'axis': {
            'domain': True,
            'domainColor': theme.get("grid_color", "#e0e0e0"),
            'domainWidth': 1,
            'domainOpacity': 0.6,
            'grid': True,
            'gridColor': theme.get("grid_color", "#e0e0e0"),
            'gridOpacity': theme.get("grid_opacity", 0.4),
            'gridWidth': 0.5,
            'gridDash': [],  # Solid lines for cleaner look
            'labelColor': theme.get("text_secondary", theme["text"]),
            'labelFont': style["font"],
            'labelFontSize': style["tick_fontsize"],
            'labelFontWeight': style["label_fontweight"],
            'labelPadding': 8,
            'labelAngle': 0,
            'ticks': True,
            'tickColor': theme.get("grid_color", "#e0e0e0"),
            'tickSize': 4,
            'tickWidth': 1,
            'tickOpacity': 0.6,
            'titleColor': theme["text"],
            'titleFont': style["font"],
            'titleFontSize': style["label_fontsize"],
            'titleFontWeight': 500,
            'titlePadding': 12,
        },
        # X-axis specific
        'axisX': {
            'labelAngle': 0,
            'labelBaseline': 'top',
        },
        # Y-axis specific  
        'axisY': {
            'labelAlign': 'right',
        },
        # Legend configuration - minimal, integrated
        'legend': {
            'labelColor': theme.get("text_secondary", theme["text"]),
            'labelFont': style["font"],
            'labelFontSize': style["legend_fontsize"],
            'labelFontWeight': style["label_fontweight"],
            'titleColor': theme["text"],
            'titleFont': style["font"],
            'titleFontSize': style.get("legend_title_fontsize", style["label_fontsize"]),
            'titleFontWeight': 500,
            'padding': 12,
            'offset': 16,
            'cornerRadius': 0,
            'strokeColor': 'transparent',
            'strokeWidth': 0,
            'symbolSize': 80,
            'symbolType': 'circle',
            'symbolStrokeWidth': 0,
            'orient': 'right',
            'direction': 'vertical',
        },
        # Title configuration - clean, left-aligned
        'title': {
            'color': theme["text"],
            'font': style["font"],
            'fontSize': style["title_fontsize"],
            'fontWeight': style["title_fontweight"],
            'anchor': 'start',
            'offset': 16,
            'subtitleColor': theme.get("text_secondary", theme["text"]),
            'subtitleFont': style["font"],
            'subtitleFontSize': style["label_fontsize"],
            'subtitleFontWeight': 400,
            'subtitlePadding': 4,
        },
        # Mark configurations
        'bar': {
            'cornerRadiusTopLeft': style["corner_radius"],
            'cornerRadiusTopRight': style["corner_radius"],
            'stroke': None,
        },
        'line': {
            'strokeWidth': style["stroke_width"],
            'strokeCap': 'round',
            'strokeJoin': 'round',
        },
        'point': {
            'size': 60,
            'strokeWidth': 0,
            'filled': True,
        },
        'circle': {
            'strokeWidth': 0,
            'filled': True,
        },
        'arc': {
            'stroke': theme["background"],
            'strokeWidth': 2,
        },
        'area': {
            'opacity': 0.7,
            'line': True,
        },
        # Range configuration for colors
        'range': {
            'category': theme.get("categorical", theme["colors"]),
            'ordinal': {'scheme': 'blues'},
            'heatmap': {'scheme': 'viridis'},
        },
        # Background
        'background': theme["background"],
        # Padding
        'padding': {'left': style["padding"], 'right': style["padding"], 
                   'top': style["padding"], 'bottom': style["padding"]},
        # Autosize
        'autosize': {'type': 'fit', 'contains': 'padding'},
    }
    
    return chart.configure(**config_dict)


def get_color_scheme(theme_name="default", n_colors=5, scheme_type="categorical"):
    """
    Returns color scheme for theme.
    
    Args:
        theme_name: Name of theme
        n_colors: Number of colors to return
        scheme_type: 'categorical', 'sequential', or 'colors' (default palette)
    
    Returns:
        List of color hex codes
    """
    theme = get_theme(theme_name)
    
    if scheme_type == "categorical":
        colors = theme.get("categorical", theme["colors"])
    elif scheme_type == "sequential":
        colors = theme.get("sequential", theme["colors"])
    else:
        colors = theme["colors"]
    
    return colors[:n_colors]


def list_themes():
    """Returns list of available themes with descriptions."""
    return {name: theme["description"] for name, theme in SOLVIEN_THEMES.items()}


def apply_corporate_style(chart, dark_mode=False):
    """Convenience function to apply professional corporate style."""
    theme_name = "corporate_dark" if dark_mode else "corporate"
    return configure_chart(chart, theme_name)


def apply_modern_style(chart, dark_mode=False):
    """Convenience function to apply modern vibrant style."""
    theme_name = "modern_dark" if dark_mode else "modern"
    return configure_chart(chart, theme_name)


def apply_minimal_style(chart):
    """Convenience function to apply minimal clean style."""
    return configure_chart(chart, "minimal")
