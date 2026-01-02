"""
Solvien Graph - Main chart functions (Altair/D3.js)
Interactive, professional and bioinformatics-focused data visualization
D3.js/Vega-Lite based, web standards compliant
"""

import altair as alt
import pandas as pd
import numpy as np
from .styles import get_theme, configure_chart, get_color_scheme, DEFAULT_STYLE, PUBLICATION_STYLE

# Configure Altair renderer
import os
import webbrowser
import tempfile
import json

# Jupyter check
IN_JUPYTER = 'JPY_PARENT_PID' in os.environ or 'IPYTHON' in os.environ


def _create_viewer_html(chart, title="Solvien Chart", default_width=800, default_height=500, theme="default"):
    """
    Creates a minimalist viewer HTML.
    Only chart display and PNG/SVG/PDF download buttons.
    """
    # Convert chart to JSON
    chart_json = chart.to_json()
    
    # Minimalist HTML template
    html_template = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: #ffffff;
      color: #212529;
      margin: 0;
      padding: 0;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .header {{
      background: #f8f9fa;
      padding: 15px 25px;
      border-bottom: 1px solid #dee2e6;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .header h1 {{
      font-size: 18px;
      font-weight: 500;
      color: #212529;
      margin: 0;
    }}
    .header-buttons {{
      display: flex;
      gap: 8px;
    }}
    .header-buttons button {{
      padding: 8px 16px;
      background: #ffffff;
      color: #212529;
      border: 1px solid #dee2e6;
      border-radius: 4px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.2s;
    }}
    .header-buttons button:hover {{
      background: #f8f9fa;
      border-color: #adb5bd;
    }}
    .header-buttons button:active {{
      background: #e9ecef;
    }}
    #vis {{
      flex: 1;
      overflow: auto;
      padding: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #ffffff;
    }}
    #vis.vega-embed {{
      width: 100%;
    }}
    .vega-actions {{
      display: none !important;
    }}
  </style>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@6"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@6.1.0"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@7"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <div class="header-buttons">
      <button onclick="exportPNG()">PNG</button>
      <button onclick="exportSVG()">SVG</button>
      <button onclick="exportPDF()">PDF</button>
    </div>
  </div>
  <div id="vis"></div>

  <script type="text/javascript">
    let chartSpec = {chart_json};
    let vegaView = null;

    function renderChart() {{
      vegaEmbed('#vis', chartSpec, {{
        actions: false,
        renderer: 'canvas'
      }}).then(function(result) {{
        vegaView = result.view;
        const embed = document.querySelector('#vis .vega-embed');
        if (embed) {{
          const menu = embed.querySelector('.vega-actions');
          if (menu) menu.remove();
        }}
      }}).catch(function(error) {{
        console.error('Chart render error: ', error);
      }});
    }}

    function exportPNG() {{
      if (vegaView) {{
        vegaView.toImageURL('png', 2).then(function(url) {{
          const link = document.createElement('a');
          link.download = '{title.replace(" ", "_").replace("/", "_").replace(":", "_")}.png';
          link.href = url;
          link.click();
        }});
      }}
    }}

    function exportSVG() {{
      if (vegaView) {{
        vegaView.toImageURL('svg').then(function(url) {{
          const link = document.createElement('a');
          link.download = '{title.replace(" ", "_").replace("/", "_").replace(":", "_")}.svg';
          link.href = url;
          link.click();
        }});
      }}
    }}

    function exportPDF() {{
      if (vegaView) {{
        vegaView.toImageURL('png', 2).then(function(url) {{
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = function() {{
            try {{
              const {{ jsPDF }} = window.jspdf;
              const pdf = new jsPDF('landscape', 'pt', [img.width, img.height]);
              pdf.addImage(img.src, 'PNG', 0, 0, img.width, img.height);
              pdf.save('{title.replace(" ", "_").replace("/", "_").replace(":", "_")}.pdf');
            }} catch (e) {{
              console.error('PDF creation error: ', e);
              exportPNG();
            }}
          }};
          img.src = url;
        }});
      }}
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

