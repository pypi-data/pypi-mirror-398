"""
Solvien Graph - Specialized chart functions for bioinformatics (Altair/D3.js)
Gene expression, differential analysis and genomic data visualization - Interactive
D3.js/Vega-Lite based
"""

import altair as alt
import pandas as pd
import numpy as np
import os
import webbrowser
import tempfile
from .styles import get_theme, configure_chart, get_bioinformatics_palette, DEFAULT_STYLE, PUBLICATION_STYLE

# Jupyter check
IN_JUPYTER = 'JPY_PARENT_PID' in os.environ or 'IPYTHON' in os.environ


def quick_heatmap(data, title="Heatmap", cmap="viridis", theme="default", 
                  figsize=None, show=True, cbar_label="Value", 
                  xticklabels=None, yticklabels=None, publication_quality=False,
                  annotate=False, cluster_rows=False, cluster_cols=False):
    """
    Creates an interactive heatmap (for gene expression, correlation matrix, etc.).
    D3.js/Vega-Lite based.
    
    Parameters:
    -----------
    data : 2D array-like
        Heatmap data (rows x columns)
    title : str
        Chart title
    cmap : str
        Color map (viridis, plasma, inferno, magma, cividis, coolwarm, rdbu)
    theme : str
        Theme name
    figsize : tuple, optional
        Chart size
    show : bool
        True to display the chart
    cbar_label : str
        Colorbar label
    xticklabels : list, optional
        X axis labels
    yticklabels : list, optional
        Y axis labels
    publication_quality : bool
        True for publication quality
    annotate : bool
        Print values on cells (for small heatmaps)
    cluster_rows : bool
        Sort rows by hierarchical clustering
    cluster_cols : bool
        Sort columns by hierarchical clustering
    
    Returns:
    --------
    chart : altair.Chart
    """
    data = np.array(data)
    rows, cols = data.shape
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width = max(800, cols * 50)
        height = max(600, rows * 30)
    
    # Clustering (if requested) - dendrogram visualization removed
    row_order = list(range(rows))
    col_order = list(range(cols))
    
    if cluster_rows or cluster_cols:
        try:
            from scipy.cluster.hierarchy import linkage, leaves_list
            from scipy.spatial.distance import pdist
            
            if cluster_rows:
                row_dist = pdist(data)
                row_linkage = linkage(row_dist, method='ward')
                row_order = leaves_list(row_linkage).tolist()
            
            if cluster_cols:
                col_dist = pdist(data.T)
                col_linkage = linkage(col_dist, method='ward')
                col_order = leaves_list(col_linkage).tolist()
            
            # Reorder data
            data = data[np.ix_(row_order, col_order)]
            if yticklabels:
                yticklabels = [yticklabels[i] for i in row_order]
            if xticklabels:
                xticklabels = [xticklabels[i] for i in col_order]
        except ImportError:
            # Don't cluster if scipy is not available
            pass
        except Exception as e:
            # Dendrogram creation error - just do clustering
            import traceback
            traceback.print_exc()
            pass
    
    # Convert data to long format
    df_list = []
    for i in range(rows):
        for j in range(cols):
            row_label = yticklabels[i] if yticklabels else f"Row_{i}"
            col_label = xticklabels[j] if xticklabels else f"Col_{j}"
            df_list.append({
                'Row': row_label,
                'Column': col_label,
                'Value': data[i, j],
                'RowIdx': i,
                'ColIdx': j
            })
    
    df = pd.DataFrame(df_list)
    
    # Altair colormap
    altair_cmaps = {
        "viridis": "viridis",
        "plasma": "plasma",
        "inferno": "inferno",
        "magma": "magma",
        "cividis": "cividis",
        "coolwarm": "blueorange",
        "rdbu": "redblue"
    }
    
    altair_cmap = altair_cmaps.get(cmap.lower(), "viridis")
    
    # Heatmap base
    base = alt.Chart(df).mark_rect().encode(
        x=alt.X('ColIdx:O', title="", 
                axis=alt.Axis(labels=False if xticklabels is None else True,
                            labelAngle=-45)),
        y=alt.Y('RowIdx:O', title="",
                axis=alt.Axis(labels=False if yticklabels is None else True)),
        color=alt.Color('Value:Q', 
                       scale=alt.Scale(scheme=altair_cmap),
                       legend=alt.Legend(title=cbar_label)),
        tooltip=['Row:N', 'Column:N', alt.Tooltip('Value:Q', format='.3f')]
    ).properties(
        width=width,
        height=height,
        title=title
    )
    
    # Text overlay (if annotate=True)
    if annotate:
        # Only show text on small heatmaps (for readability)
        if rows <= 30 and cols <= 20:
            text_layer = alt.Chart(df).mark_text(
                align='center',
                baseline='middle',
                font=style["font"],
                fontSize=style["tick_fontsize"],
                fontWeight=500
            ).encode(
                x=alt.X('ColIdx:O', title=""),
                y=alt.Y('RowIdx:O', title=""),
                text=alt.Text('Value:Q', format='.2f'),
                color=alt.condition(
                    alt.datum.Value > (df['Value'].max() + df['Value'].min()) / 2,
                    alt.value('white'),
                    alt.value('black')
                )
            )
            chart = (base + text_layer).resolve_scale(color='independent')
        else:
            chart = base
    else:
        chart = base
    
    # Dendrogram visualization removed
    # Clustering ordering is still applied (done above)
    
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            # Create HTML file (in main directory - working directory)
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            # Main directory (working directory)
            current_dir = Path.cwd()
            
            # Create unique file name
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            html_file = current_dir / f'solvien_chart_{timestamp}.html'
            
            # Create PNG, SVG files
            from .core import _export_chart_files, _create_viewer_html
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
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


def quick_volcano(log2fc, pvalue, title="Volcano Plot", theme="default",
                  fc_threshold=1.0, pvalue_threshold=0.05, figsize=None, 
                  show=True, labels=None, publication_quality=False):
    """
    Creates an interactive volcano plot (for differential gene expression analysis).
    D3.js/Vega-Lite based.
    
    Parameters:
    -----------
    log2fc : array-like
        Log2 fold change values
    pvalue : array-like
        P-value values
    title : str
        Chart title
    theme : str
        Theme name
    fc_threshold : float
        Fold change threshold value
    pvalue_threshold : float
        P-value threshold value
    figsize : tuple, optional
        Chart size
    show : bool
        True to display the chart
    labels : array-like, optional
        Gene names (for significant genes)
    publication_quality : bool
        True for publication quality
    
    Returns:
    --------
    chart : altair.Chart
    """
    log2fc = np.array(log2fc)
    pvalue = np.array(pvalue)
    neg_log10_p = -np.log10(pvalue + 1e-300)
    
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width, height = style["width"], style["height"]
    
    # Identify significant genes
    significant = (np.abs(log2fc) >= fc_threshold) & (pvalue <= pvalue_threshold)
    upregulated = significant & (log2fc > 0)
    downregulated = significant & (log2fc < 0)
    not_significant = ~significant
    
    # Convert data to DataFrame
    df = pd.DataFrame({
        'Log2FC': log2fc,
        'NegLog10P': neg_log10_p,
        'Category': ['Upregulated' if up else 'Downregulated' if down else 'Not significant' 
                     for up, down in zip(upregulated, downregulated)],
        'Label': labels if labels is not None else [f"Gene_{i+1}" for i in range(len(log2fc))]
    })
    
    # Volcano plot
    base = alt.Chart(df).mark_circle(size=60, opacity=0.7).encode(
        x=alt.X('Log2FC:Q', title="Log₂ Fold Change"),
        y=alt.Y('NegLog10P:Q', title="-Log₁₀ P-value"),
        color=alt.Color('Category:N', 
                       scale=alt.Scale(domain=['Not significant', 'Upregulated', 'Downregulated'],
                                     range=[theme_obj.get("secondary", "#cccccc"), '#d62728', '#1f77b4'])),
        tooltip=['Label:N', alt.Tooltip('Log2FC:Q', format='.2f'), 
                alt.Tooltip('NegLog10P:Q', format='.2f')]
    ).properties(
        width=width,
        height=height,
        title=title
    )
    
    # Add gene names (if labels exist and for significant genes)
    if labels is not None:
        # Only show labels for significant genes
        df_labels = df[df['Category'] != 'Not significant'].copy()
        if len(df_labels) > 0:
            text_layer = alt.Chart(df_labels).mark_text(
                align='left',
                baseline='middle',
                font=style["font"],
                fontSize=style["tick_fontsize"],
                fontWeight=500,
                dx=5,  # Shift right on X axis
                dy=-5  # Shift up on Y axis
            ).encode(
                x=alt.X('Log2FC:Q', title="Log₂ Fold Change"),
                y=alt.Y('NegLog10P:Q', title="-Log₁₀ P-value"),
                text='Label:N',
                color=alt.Color('Category:N',
                               scale=alt.Scale(domain=['Upregulated', 'Downregulated'],
                                             range=['#d62728', '#1f77b4']))
            )
            chart = (base + text_layer).resolve_scale(color='independent')
        else:
            chart = base
    else:
        chart = base
    
    # Add threshold lines
    # Vertical lines (FC thresholds)
    vline1 = alt.Chart(pd.DataFrame({'x': [fc_threshold]})).mark_rule(
        strokeDash=[5, 5], opacity=0.5, color=theme_obj["text"]
    ).encode(x='x:Q')
    
    vline2 = alt.Chart(pd.DataFrame({'x': [-fc_threshold]})).mark_rule(
        strokeDash=[5, 5], opacity=0.5, color=theme_obj["text"]
    ).encode(x='x:Q')
    
    # Horizontal line (p-value threshold)
    hline = alt.Chart(pd.DataFrame({'y': [-np.log10(pvalue_threshold)]})).mark_rule(
        strokeDash=[5, 5], opacity=0.5, color=theme_obj["text"]
    ).encode(y='y:Q')
    
    chart = (chart + vline1 + vline2 + hline)
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            # Create HTML file (in main directory - working directory)
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            # Main directory (working directory)
            current_dir = Path.cwd()
            
            # Create unique file name
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            html_file = current_dir / f'solvien_chart_{timestamp}.html'
            
            # Create PNG, SVG files
            from .core import _export_chart_files, _create_viewer_html
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
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


def quick_ma_plot(mean_expr, log2fc, title="MA Plot", theme="default",
                  figsize=None, show=True, publication_quality=False):
    """
    Creates an interactive MA plot (for differential expression analysis).
    D3.js/Vega-Lite based.
    
    Parameters:
    -----------
    mean_expr : array-like
        Mean expression values
    log2fc : array-like
        Log2 fold change values
    title : str
        Chart title
    theme : str
        Theme name
    figsize : tuple, optional
        Chart size
    show : bool
        True to display the chart
    publication_quality : bool
        True for publication quality
    
    Returns:
    --------
    chart : altair.Chart
    """
    mean_expr = np.array(mean_expr)
    log2fc = np.array(log2fc)
    
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    if figsize:
        width, height = figsize
    else:
        width, height = style["width"], style["height"]
    
    df = pd.DataFrame({
        'MeanExpr': mean_expr,
        'Log2FC': log2fc
    })
    
    chart = alt.Chart(df).mark_circle(size=30, opacity=0.6).encode(
        x=alt.X('MeanExpr:Q', title="Mean Expression (Log)"),
        y=alt.Y('Log2FC:Q', title="Log₂ Fold Change"),
        color=alt.value(theme_obj["accent"]),
        tooltip=[alt.Tooltip('MeanExpr:Q', format='.2f'), 
                alt.Tooltip('Log2FC:Q', format='.2f')]
    ).properties(
        width=width,
        height=height,
        title=title
    )
    
    # Horizontal line (FC=0)
    zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
        strokeDash=[5, 5], opacity=0.5, color=theme_obj["text"]
    ).encode(y='y:Q')
    
    chart = (chart + zero_line)
    chart = configure_chart(chart, theme, publication_quality)
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            # Create HTML file (in main directory - working directory)
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            # Main directory (working directory)
            current_dir = Path.cwd()
            
            # Create unique file name
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            html_file = current_dir / f'solvien_chart_{timestamp}.html'
            
            # Create PNG, SVG files
            from .core import _export_chart_files, _create_viewer_html
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
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


def quick_violin(data_dict, title="Violin Plot", theme="default",
                 figsize=None, show=True, publication_quality=False):
    """
    Creates an interactive violin plot (for distribution visualization).
    Uses Altair's density transform for proper violin shape.
    
    Parameters:
    -----------
    data_dict : dict
        Data in {category: values} format
    title : str
        Chart title
    theme : str
        Theme name
    figsize : tuple, optional
        Chart size
    show : bool
        True to display the chart
    publication_quality : bool
        True for publication quality
    
    Returns:
    --------
    chart : altair.Chart
    """
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    n_categories = len(data_dict)
    categories = list(data_dict.keys())
    
    if figsize:
        width, height = figsize
    else:
        width = max(100, 600 // n_categories)
        height = style["height"]
    
    # Convert to DataFrame
    df_list = []
    for cat, values in data_dict.items():
        for val in np.array(values):
            df_list.append({'Category': cat, 'Value': val})
    df = pd.DataFrame(df_list)
    
    colors = theme_obj["colors"][:n_categories]
    
    # Calculate extent
    val_min = df['Value'].min()
    val_max = df['Value'].max()
    padding = (val_max - val_min) * 0.1
    extent = [val_min - padding, val_max + padding]
    
    # Create violin using official Altair syntax
    chart = alt.Chart(df, width=width).transform_density(
        'Value',
        as_=['Value', 'density'],
        extent=extent,
        groupby=['Category']
    ).mark_area(orient='horizontal').encode(
        alt.X('density:Q')
            .stack('center')
            .impute(None)
            .title(None)
            .axis(labels=False, values=[0], grid=False, ticks=True),
        alt.Y('Value:Q').title('Value'),
        alt.Color('Category:N').scale(domain=categories, range=colors).legend(None),
        alt.Column('Category:N')
            .spacing(0)
            .header(titleOrient='bottom', labelOrient='bottom', labelPadding=0)
    ).properties(
        height=height,
        title=title
    ).configure_view(
        stroke=None
    )
    
    if show:
        if IN_JUPYTER:
            chart.show()
        else:
            from urllib.request import pathname2url
            from pathlib import Path
            import datetime
            
            current_dir = Path.cwd()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            
            from .core import _export_chart_files, _create_viewer_html
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
            files_created = _export_chart_files(chart, title, base_name, current_dir)
            
            try:
                html_file = current_dir / f'{base_name}.html'
                total_width = n_categories * width + 100
                html_content = _create_viewer_html(chart, title, total_width, height, theme)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                if html_file.exists():
                    files_created.append(str(html_file))
                    print(f"✅ HTML viewer created: {html_file.name}")
                    
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


def quick_boxplot(data_dict, title="Box Plot", theme="default",
                  figsize=None, show=True, horizontal=False, publication_quality=False):
    """
    Creates an interactive box plot.
    D3.js/Vega-Lite based.
    
    Parameters:
    -----------
    data_dict : dict
        Data in {category: values} format
    title : str
        Chart title
    theme : str
        Theme name
    figsize : tuple, optional
        Chart size
    show : bool
        True to display the chart
    horizontal : bool
        True for horizontal box plot
    publication_quality : bool
        True for publication quality
    
    Returns:
    --------
    chart : altair.Chart
    """
    theme_obj = get_theme(theme)
    style = PUBLICATION_STYLE if publication_quality else DEFAULT_STYLE
    
    # Dynamic width based on number of categories
    n_categories = len(data_dict)
    
    if figsize:
        width, height = figsize
    else:
        # At least 100px per category, minimum chart width
        width = max(style["width"], n_categories * 120)
        height = style["height"]
    
    # Convert data to DataFrame
    df_list = []
    for cat, values in data_dict.items():
        for val in np.array(values):
            df_list.append({'Category': cat, 'Value': val})
    
    df = pd.DataFrame(df_list)
    colors = theme_obj["colors"][:len(data_dict)]
    
    # Dynamic box size based on category count
    box_size = max(30, min(60, 300 // n_categories))
    
    chart = alt.Chart(df).mark_boxplot(size=box_size).encode(
        x=alt.X('Category:N' if not horizontal else 'Value:Q', 
                title=None if not horizontal else "Value",
                axis=alt.Axis(labelAngle=-45 if n_categories > 4 else 0, labelLimit=150)),
        y=alt.Y('Value:Q' if not horizontal else 'Category:N', 
                title="Value" if not horizontal else None),
        color=alt.Color('Category:N', scale=alt.Scale(range=colors), legend=None),
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
            # Create HTML file (in main directory - working directory)
            from urllib.request import pathname2url
            import time
            from pathlib import Path
            import datetime
            
            # Main directory (working directory)
            current_dir = Path.cwd()
            
            # Create unique file name
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            html_file = current_dir / f'solvien_chart_{timestamp}.html'
            
            # Create PNG, SVG files
            from .core import _export_chart_files, _create_viewer_html
            safe_title = title.replace(" ", "_").replace("/", "_").replace(":", "_")
            base_name = f'{safe_title}_{timestamp}'
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
