"""
Solvien Graph - Main chart functions (Altair/D3.js)
Interactive, professional and bioinformatics-focused data visualization
D3.js/Vega-Lite based, web standards compliant
"""

import altair as alt
import pandas as pd
import numpy as np
from .styles import get_theme, configure_chart, get_color_scheme, get_style_for_theme, DEFAULT_STYLE, PUBLICATION_STYLE

# Configure Altair renderer
import os
import webbrowser
import tempfile
import json

# Jupyter check
IN_JUPYTER = 'JPY_PARENT_PID' in os.environ or 'IPYTHON' in os.environ


def _create_viewer_html(chart, title="Solvien Chart", default_width=800, default_height=500, theme="default"):
    """
    Creates a professional, minimalist viewer HTML.
    Enterprise-grade clean design.
    """
    # Convert chart to JSON
    chart_json = chart.to_json()
    
    # Determine if dark mode
    is_dark = theme in ["corporate_dark", "modern_dark"]
    
    # Theme-based colors
    if is_dark:
        bg_color = "#161616"
        header_bg = "#262626"
        text_color = "#f4f4f4"
        text_secondary = "#c6c6c6"
        border_color = "#393939"
        btn_bg = "#393939"
        btn_hover = "#4d4d4d"
        accent = "#78a9ff" if theme == "corporate_dark" else "#8AB4F8"
    else:
        bg_color = "#ffffff"
        header_bg = "#f4f4f4"
        text_color = "#161616"
        text_secondary = "#525252"
        border_color = "#e0e0e0"
        btn_bg = "#ffffff"
        btn_hover = "#f4f4f4"
        accent = "#0f62fe" if theme == "corporate" else "#4285F4"
    
    # Professional minimalist HTML template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Solvien Graph</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    
    body {{
      font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: {bg_color};
      color: {text_color};
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}
    
    /* Header - Clean & Minimal */
    .header {{
      background: {header_bg};
      padding: 16px 32px;
      border-bottom: 1px solid {border_color};
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }}
    
    .header-title {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    
    .header h1 {{
      font-size: 14px;
      font-weight: 500;
      color: {text_color};
      letter-spacing: 0.16px;
    }}
    
    .header-badge {{
      font-size: 11px;
      font-weight: 500;
      color: {text_secondary};
      background: {border_color};
      padding: 2px 8px;
      border-radius: 2px;
      letter-spacing: 0.32px;
      text-transform: uppercase;
    }}
    
    /* Export Buttons - IBM Carbon Style */
    .header-actions {{
      display: flex;
      gap: 1px;
      background: {border_color};
      border-radius: 0;
    }}
    
    .btn {{
      padding: 10px 16px;
      background: {btn_bg};
      color: {text_color};
      border: none;
      cursor: pointer;
      font-family: inherit;
      font-size: 14px;
      font-weight: 400;
      letter-spacing: 0.16px;
      transition: background-color 0.15s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    
    .btn:first-child {{
      border-radius: 0;
    }}
    
    .btn:last-child {{
      border-radius: 0;
    }}
    
    .btn:hover {{
      background: {btn_hover};
    }}
    
    .btn:active {{
      background: {accent};
      color: #ffffff;
    }}
    
    .btn svg {{
      width: 16px;
      height: 16px;
      fill: currentColor;
    }}
    
    /* Chart Container */
    .chart-container {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 48px;
      overflow: auto;
    }}
    
    #vis {{
      background: {bg_color};
    }}
    
    .vega-embed {{
      width: auto !important;
    }}
    
    .vega-actions {{
      display: none !important;
    }}
    
    /* Footer */
    .footer {{
      padding: 12px 32px;
      border-top: 1px solid {border_color};
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: {text_secondary};
      background: {header_bg};
      flex-shrink: 0;
    }}
    
    .footer a {{
      color: {accent};
      text-decoration: none;
    }}
    
    .footer a:hover {{
      text-decoration: underline;
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
      .header {{
        padding: 12px 16px;
      }}
      .chart-container {{
        padding: 24px 16px;
      }}
      .btn {{
        padding: 8px 12px;
        font-size: 13px;
      }}
    }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
</head>
<body>
  <header class="header">
    <div class="header-title">
      <h1>{title}</h1>
      <span class="header-badge">Solvien Graph</span>
    </div>
    <div class="header-actions">
      <button class="btn" onclick="exportPNG()" title="Download PNG">
        <svg viewBox="0 0 16 16"><path d="M2 14h12v1H2zM8 12L4 8l.7-.7L7.5 10V1h1v9l2.8-2.7.7.7z"/></svg>
        PNG
      </button>
      <button class="btn" onclick="exportSVG()" title="Download SVG">
        <svg viewBox="0 0 16 16"><path d="M2 14h12v1H2zM8 12L4 8l.7-.7L7.5 10V1h1v9l2.8-2.7.7.7z"/></svg>
        SVG
      </button>
      <button class="btn" onclick="exportPDF()" title="Download PDF">
        <svg viewBox="0 0 16 16"><path d="M2 14h12v1H2zM8 12L4 8l.7-.7L7.5 10V1h1v9l2.8-2.7.7.7z"/></svg>
        PDF
      </button>
    </div>
  </header>
  
  <main class="chart-container">
    <div id="vis"></div>
  </main>
  
  <footer class="footer">
    <span>Generated with Solvien Graph</span>
    <span>Interactive D3.js/Vega-Lite visualization</span>
  </footer>

  <script>
    const chartSpec = {chart_json};
    let vegaView = null;

    async function renderChart() {{
      try {{
        const result = await vegaEmbed('#vis', chartSpec, {{
          actions: false,
          renderer: 'canvas',
          padding: 0
        }});
        vegaView = result.view;
      }} catch (error) {{
        console.error('Chart render error:', error);
        document.getElementById('vis').innerHTML = '<p style="color: #da1e28;">Error rendering chart</p>';
      }}
    }}

    async function exportPNG() {{
      if (!vegaView) return;
      try {{
        const url = await vegaView.toImageURL('png', 2);
        downloadFile(url, '{title.replace(" ", "_").replace("/", "_").replace(":", "_")}.png');
      }} catch (e) {{
        console.error('PNG export error:', e);
      }}
    }}

    async function exportSVG() {{
      if (!vegaView) return;
      try {{
        const url = await vegaView.toImageURL('svg');
        downloadFile(url, '{title.replace(" ", "_").replace("/", "_").replace(":", "_")}.svg');
      }} catch (e) {{
        console.error('SVG export error:', e);
      }}
    }}

    async function exportPDF() {{
      if (!vegaView) return;
      try {{
        const url = await vegaView.toImageURL('png', 2);
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = function() {{
          const {{ jsPDF }} = window.jspdf;
          const pdf = new jsPDF('landscape', 'pt', [img.width, img.height]);
          pdf.addImage(img.src, 'PNG', 0, 0, img.width, img.height);
          pdf.save('{title.replace(" ", "_").replace("/", "_").replace(":", "_")}.pdf');
        }};
        img.src = url;
      }} catch (e) {{
        console.error('PDF export error:', e);
      }}
    }}

    function downloadFile(url, filename) {{
      const link = document.createElement('a');
      link.download = filename;
      link.href = url;
      link.click();
    }}

    renderChart();
  </script>
</body>
</html>"""
    
    return html_template


def _export_chart_files(chart, title, base_name, current_dir):
    """
    Saves chart as PNG, SVG and PDF.
    """
    files_created = []
    
    # Create PNG
    try:
        png_file = current_dir / f'{base_name}.png'
        chart.save(str(png_file), format='png', scale_factor=2)
        if png_file.exists():
            files_created.append(str(png_file))
            print(f"✅ PNG created: {png_file.name}")
    except Exception as e:
        print(f"⚠️  PNG could not be created: {e}")
    
    # Create SVG
    try:
        svg_file = current_dir / f'{base_name}.svg'
        chart.save(str(svg_file), format='svg')
        if svg_file.exists():
            files_created.append(str(svg_file))
            print(f"✅ SVG created: {svg_file.name}")
    except Exception as e:
        print(f"⚠️  SVG could not be created: {e}")
    
    # Create PDF
    try:
        pdf_file = current_dir / f'{base_name}.pdf'
        chart.save(str(pdf_file), format='pdf')
        if pdf_file.exists():
            files_created.append(str(pdf_file))
            print(f"✅ PDF created: {pdf_file.name}")
    except Exception as e:
        print(f"⚠️  PDF could not be created: {e}")
    
    return files_created


def quick_bar(data, title="Solvien Graph", color=None, theme="default", 
              figsize=None, show=True, publication_quality=False, 
              xlabel="Category", ylabel="Value"):
    """Creates an interactive bar chart (D3.js/Vega-Lite based)."""
    df = pd.DataFrame({
        'Category': list(data.keys()),
        'Value': list(data.values())
    })
    
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width, height = style["width"], style["height"]
    
    if color is None:
        if len(df) == 1:
            color = theme_obj["colors"][0]
        else:
            color = alt.Color('Category:N', scale=alt.Scale(range=theme_obj["colors"][:len(df)]))
    
    chart = alt.Chart(df).mark_bar(
        cornerRadiusTopLeft=2,
        cornerRadiusTopRight=2
    ).encode(
        x=alt.X('Category:N', title=xlabel, sort='-y'),
        y=alt.Y('Value:Q', title=ylabel),
        color=color if isinstance(color, (str, list)) else color,
        tooltip=['Category:N', alt.Tooltip('Value:Q', format='.2f')]
    ).properties(
        width=width,
        height=height,
        title=title
    )
    
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            current_dir = Path.cwd()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
            
            # Create PNG, SVG files
            files_created = _export_chart_files(chart, title, base_name, current_dir)
            
            # Create HTML viewer
            try:
                html_file = current_dir / f'{base_name}.html'
                html_content = _create_viewer_html(chart, title, width, height, theme)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                if html_file.exists():
                    files_created.append(str(html_file))
                    print(f"✅ HTML viewer created: {html_file.name}")
                    
                    # Open HTML in browser
                    html_file_abs = str(html_file.absolute())
                    file_url = 'file://' + pathname2url(html_file_abs)
                    try:
                        webbrowser.open(file_url)
                        print(f"📊 HTML opened in browser")
                    except Exception as e:
                        print(f"⚠️  Browser could not be opened: {e}")
            except Exception as e:
                print(f"⚠️  HTML could not be created: {e}")
            
            if files_created:
                print(f"\n📁 Created files:")
                for f in files_created:
                    print(f"   - {Path(f).name}")
    
    return chart


def quick_line(x, y, title="Solvien Line Chart", color=None, theme="default", 
               figsize=None, show=True, marker=True, linewidth=2, 
               publication_quality=False, xlabel="X Axis", ylabel="Y Axis"):
    """Creates an interactive line chart (D3.js/Vega-Lite based)."""
    df = pd.DataFrame({
        'X': np.array(x),
        'Y': np.array(y)
    })
    
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width, height = style["width"], style["height"]
    
    if color is None:
        color = theme_obj["colors"][0]
    
    if marker:
        chart = alt.Chart(df).mark_line(point=True, strokeWidth=linewidth).encode(
            x=alt.X('X:Q', title=xlabel),
            y=alt.Y('Y:Q', title=ylabel),
            color=alt.value(color),
            tooltip=[alt.Tooltip('X:Q', format='.2f'), alt.Tooltip('Y:Q', format='.2f')]
        ).properties(
            width=width,
            height=height,
            title=title
        )
    else:
        chart = alt.Chart(df).mark_line(strokeWidth=linewidth).encode(
            x=alt.X('X:Q', title=xlabel),
            y=alt.Y('Y:Q', title=ylabel),
            color=alt.value(color),
            tooltip=[alt.Tooltip('X:Q', format='.2f'), alt.Tooltip('Y:Q', format='.2f')]
        ).properties(
            width=width,
            height=height,
            title=title
        )
    
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            current_dir = Path.cwd()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
            
            # Create PNG, SVG files
            files_created = _export_chart_files(chart, title, base_name, current_dir)
            
            # Create HTML viewer
            try:
                html_file = current_dir / f'{base_name}.html'
                html_content = _create_viewer_html(chart, title, width, height, theme)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                if html_file.exists():
                    files_created.append(str(html_file))
                    print(f"✅ HTML viewer created: {html_file.name}")
                    
                    # Open HTML in browser
                    html_file_abs = str(html_file.absolute())
                    file_url = 'file://' + pathname2url(html_file_abs)
                    try:
                        webbrowser.open(file_url)
                        print(f"📊 HTML opened in browser")
                    except Exception as e:
                        print(f"⚠️  Browser could not be opened: {e}")
            except Exception as e:
                print(f"⚠️  HTML could not be created: {e}")
            
            if files_created:
                print(f"\n📁 Created files:")
                for f in files_created:
                    print(f"   - {Path(f).name}")
    
    return chart


def quick_scatter(x, y, title="Solvien Scatter Plot", color=None, theme="default", 
                  figsize=None, show=True, size=50, opacity=0.7, publication_quality=False,
                  xlabel="X Axis", ylabel="Y Axis"):
    """Creates an interactive scatter plot (D3.js/Vega-Lite based)."""
    df = pd.DataFrame({
        'X': np.array(x),
        'Y': np.array(y)
    })
    
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width, height = style["width"], style["height"]
    
    if color is None:
        color = theme_obj["colors"][0]
    
    chart = alt.Chart(df).mark_circle(
        size=size,
        opacity=opacity,
        stroke='white',
        strokeWidth=1
    ).encode(
        x=alt.X('X:Q', title=xlabel),
        y=alt.Y('Y:Q', title=ylabel),
        color=alt.value(color),
        tooltip=[alt.Tooltip('X:Q', format='.2f'), alt.Tooltip('Y:Q', format='.2f')]
    ).properties(
        width=width,
        height=height,
        title=title
    )
    
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            current_dir = Path.cwd()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
            
            # Create PNG, SVG files
            files_created = _export_chart_files(chart, title, base_name, current_dir)
            
            # Create HTML viewer
            try:
                html_file = current_dir / f'{base_name}.html'
                html_content = _create_viewer_html(chart, title, width, height, theme)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                if html_file.exists():
                    files_created.append(str(html_file))
                    print(f"✅ HTML viewer created: {html_file.name}")
                    
                    # Open HTML in browser
                    html_file_abs = str(html_file.absolute())
                    file_url = 'file://' + pathname2url(html_file_abs)
                    try:
                        webbrowser.open(file_url)
                        print(f"📊 HTML opened in browser")
                    except Exception as e:
                        print(f"⚠️  Browser could not be opened: {e}")
            except Exception as e:
                print(f"⚠️  HTML could not be created: {e}")
            
            if files_created:
                print(f"\n📁 Created files:")
                for f in files_created:
                    print(f"   - {Path(f).name}")
    
    return chart


def quick_pie(data, title="Solvien Pie Chart", theme="default", figsize=None, 
              show=True, publication_quality=False):
    """Creates an interactive pie chart (D3.js/Vega-Lite based)."""
    df = pd.DataFrame({
        'Category': list(data.keys()),
        'Value': list(data.values())
    })
    
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width, height = style["width"], style["height"]
    
    colors = theme_obj["colors"][:len(df)]
    
    chart = alt.Chart(df).mark_arc(
        innerRadius=0,
        outerRadius=min(width, height) / 2 - 40,
        stroke='white',
        strokeWidth=2
    ).encode(
        theta=alt.Theta('Value:Q', stack=True),
        color=alt.Color('Category:N', scale=alt.Scale(range=colors)),
        tooltip=['Category:N', alt.Tooltip('Value:Q', format='.2f'), 
                alt.Tooltip('Value:Q', format='.1%', title='Percentage')]
    ).properties(
        width=width,
        height=height,
        title=title
    )
    
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            current_dir = Path.cwd()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
            
            # Create PNG, SVG files
            files_created = _export_chart_files(chart, title, base_name, current_dir)
            
            # Create HTML viewer
            try:
                html_file = current_dir / f'{base_name}.html'
                html_content = _create_viewer_html(chart, title, width, height, theme)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                if html_file.exists():
                    files_created.append(str(html_file))
                    print(f"✅ HTML viewer created: {html_file.name}")
                    
                    # Open HTML in browser
                    html_file_abs = str(html_file.absolute())
                    file_url = 'file://' + pathname2url(html_file_abs)
                    try:
                        webbrowser.open(file_url)
                        print(f"📊 HTML opened in browser")
                    except Exception as e:
                        print(f"⚠️  Browser could not be opened: {e}")
            except Exception as e:
                print(f"⚠️  HTML could not be created: {e}")
            
            if files_created:
                print(f"\n📁 Created files:")
                for f in files_created:
                    print(f"   - {Path(f).name}")
    
    return chart


def quick_hist(data, title="Solvien Histogram", color=None, theme="default", 
               figsize=None, show=True, bins=30, opacity=0.7, publication_quality=False,
               xlabel="Value", ylabel="Frequency"):
    """Creates an interactive histogram (D3.js/Vega-Lite based)."""
    df = pd.DataFrame({
        'Value': np.array(data)
    })
    
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width, height = style["width"], style["height"]
    
    if color is None:
        color = theme_obj["colors"][0]
    
    chart = alt.Chart(df).mark_bar(
        opacity=opacity,
        stroke='white',
        strokeWidth=1.2,
        cornerRadiusTopLeft=2,
        cornerRadiusTopRight=2
    ).encode(
        x=alt.X('Value:Q', title=xlabel, bin=alt.Bin(maxbins=bins)),
        y=alt.Y('count():Q', title=ylabel),
        color=alt.value(color),
        tooltip=[alt.Tooltip('Value:Q', bin=True, format='.2f'), 
                alt.Tooltip('count():Q', title='Frequency')]
    ).properties(
        width=width,
        height=height,
        title=title
    )
    
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            current_dir = Path.cwd()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
            
            # Create PNG, SVG files
            files_created = _export_chart_files(chart, title, base_name, current_dir)
            
            # Create HTML viewer
            try:
                html_file = current_dir / f'{base_name}.html'
                html_content = _create_viewer_html(chart, title, width, height, theme)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                if html_file.exists():
                    files_created.append(str(html_file))
                    print(f"✅ HTML viewer created: {html_file.name}")
                    
                    # Open HTML in browser
                    html_file_abs = str(html_file.absolute())
                    file_url = 'file://' + pathname2url(html_file_abs)
                    try:
                        webbrowser.open(file_url)
                        print(f"📊 HTML opened in browser")
                    except Exception as e:
                        print(f"⚠️  Browser could not be opened: {e}")
            except Exception as e:
                print(f"⚠️  HTML could not be created: {e}")
            
            if files_created:
                print(f"\n📁 Created files:")
                for f in files_created:
                    print(f"   - {Path(f).name}")
    
    return chart

