"""
HTML generation for data visualization
"""

import json
import math
import html
import pandas as pd
from typing import Any, Dict, List, Union
from datetime import datetime


def _escape(s: Any) -> str:
    return html.escape("" if s is None else str(s))

def _fmt_num(x: Any, ndigits: int = 3) -> str:
    try:
        if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
            return ""
        if isinstance(x, (int, float)):
            return f"{x:.{ndigits}f}" if isinstance(x, float) else str(x)
    except Exception:
        pass
    return str(x)

def _df_kpi_bar(df: pd.DataFrame) -> str:
    """A compact KPI strip for dense experiment emails."""
    # numeric columns summary
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    kpis = []

    kpis.append(("Rows", str(df.shape[0])))
    kpis.append(("Cols", str(df.shape[1])))
    if num_cols:
        # pick a "score-like" column if exists
        score_like = None
        lower_cols = {c.lower(): c for c in df.columns}
        for key in ["score", "q", "q_score", "q-score", "acc", "success", "sr", "reward"]:
            if key in lower_cols:
                score_like = lower_cols[key]
                break

        if score_like is None:
            score_like = num_cols[0]

        s = pd.to_numeric(df[score_like], errors="coerce").dropna()
        if len(s) > 0:
            kpis.append(("Metric", _escape(score_like)))
            kpis.append(("Mean", _fmt_num(float(s.mean()), 3)))
            kpis.append(("Best", _fmt_num(float(s.max()), 3)))
            kpis.append(("Worst", _fmt_num(float(s.min()), 3)))

    # render (use table for email compatibility)
    cells = []
    for label, value in kpis[:6]:  # keep it compact
        cells.append(f"""
        <td class="kpi">
          <div class="kpi-label">{_escape(label)}</div>
          <div class="kpi-value">{_escape(value)}</div>
        </td>
        """)

    return f"""
    <table class="kpi-table" role="presentation" cellspacing="0" cellpadding="0">
      <tr>
        {''.join(cells)}
      </tr>
    </table>
    """


def _get_css() -> str:
    """Get CSS styles for the HTML."""
    return """
    :root{
      --bg:#f6f7fb;
      --card:#ffffff;
      --text:#0f172a;
      --muted:#64748b;
      --border:#e2e8f0;

      /* personality: a calm “ink blue” accent */
      --accent:#2563eb;
      --accent2:#0ea5e9;
      --accent-weak: rgba(37,99,235,.10);

      --radius:14px;
      --shadow: 0 1px 2px rgba(15,23,42,.06), 0 10px 28px rgba(15,23,42,.08);
    }

    *{ margin:0; padding:0; box-sizing:border-box; }

    body{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 22px 14px;
      font-size: 14px;
      line-height: 1.65;
      letter-spacing: -0.01em;
    }

    .container{
      max-width: 860px; /* denser email-friendly width */
      margin: 0 auto;
      background: var(--card);
      border-radius: var(--radius);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    header{
      padding: 20px 22px 14px 22px;
      border-bottom: 1px solid var(--border);
      background:
        radial-gradient(1200px 400px at 10% 0%, rgba(37,99,235,.12) 0%, rgba(37,99,235,0) 60%),
        radial-gradient(900px 320px at 90% 10%, rgba(14,165,233,.10) 0%, rgba(14,165,233,0) 55%),
        #fff;
      text-align: left;
    }

    header h1{
      font-size: 22px;
      line-height: 1.25;
      font-weight: 700;
    }

    .timestamp{
      margin-top: 6px;
      color: var(--muted);
      font-size: 12.5px;
    }

    main{ padding: 16px 22px 22px 22px; }

    .data-section{ margin-top: 16px; }
    .data-section:first-child{ margin-top: 0; }

    .data-section h2{
      font-size: 13px;
      font-weight: 700;
      color: var(--text);
      margin: 0 0 10px 0;
      padding-left: 10px;
      border-left: 3px solid var(--accent);
    }

    /* KPI strip */
    .kpi-table{ width: 100%; border-collapse: separate; border-spacing: 10px; margin-top: 10px; }
    .kpi{
      background: rgba(15,23,42,.02);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 12px;
      vertical-align: top;
    }
    .kpi-label{ font-size: 11.5px; color: var(--muted); }
    .kpi-value{
      margin-top: 4px;
      font-size: 16px;
      font-weight: 750;
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
    }

    /* Table */
    table.dataframe{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin-top: 10px;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      background: #fff;
    }

    table.dataframe thead th{
      background: #f1f5f9;
      color: var(--text);
      font-weight: 700;
      font-size: 12.5px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }

    table.dataframe tbody td{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      font-size: 13px;
      color: var(--text);
      vertical-align: middle;
    }
    table.dataframe tbody tr:last-child td{ border-bottom: none; }

    .col-index{ color: var(--muted); width: 44px; white-space: nowrap; }
    .num{
      text-align: right;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }

    /* score spark bar */
    .spark{
      margin-top: 6px;
      height: 6px;
      background: rgba(15,23,42,.06);
      border-radius: 999px;
      overflow: hidden;
    }
    .spark > span{
      display: block;
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, rgba(37,99,235,.55), rgba(14,165,233,.65));
      border-radius: 999px;
    }

    /* dict/list blocks (keep your existing style but lighter) */
    .dict-item, .list-item{
      background: #fff;
      border: 1px solid var(--border);
      padding: 12px 12px;
      margin: 8px 0;
      border-radius: 12px;
    }
    .dict-key{ font-weight: 700; color: var(--accent); margin-right: 8px; }
    .dict-value{ color: var(--text); }

    .simple-value{
      background: rgba(15,23,42,.02);
      border: 1px solid var(--border);
      padding: 14px;
      border-radius: 12px;
      text-align: left;
    }
    .simple-value pre{
      margin:0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12.5px;
      line-height: 1.6;
    }

    .json-preview{
      margin-top: 8px;
      background: #0b1220;
      color: #e5e7eb;
      padding: 12px;
      border-radius: 12px;
      overflow-x: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12px;
      line-height: 1.6;
      border: 1px solid rgba(226,232,240,.15);
    }

    .footer{
      margin-top: 14px;
      padding-top: 14px;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 12.5px;
    }

    @media (max-width: 520px){
      body{ padding: 14px 10px; }
      header, main{ padding-left: 14px; padding-right: 14px; }
      .kpi-table{ border-spacing: 8px; }
    }

    @media (prefers-color-scheme: dark){
      :root{
        --bg:#0b1220;
        --card:#0f172a;
        --text:#e5e7eb;
        --muted:#94a3b8;
        --border: rgba(148,163,184,.18);
        --shadow: none;
      }
      header{ background: #0f172a; }
      table.dataframe thead th{ background: rgba(148,163,184,.10); }
      .kpi{ background: rgba(226,232,240,.04); }
      .spark{ background: rgba(226,232,240,.10); }
      .json-preview{ background: #0b1220; }
    }
    """


def _dataframe_to_html(df: pd.DataFrame) -> str:
    """Convert pandas DataFrame to a dense, premium email-friendly HTML table."""
    html_parts = []
    html_parts.append('<div class="data-section">')
    html_parts.append('<h2>DataFrame</h2>')
    html_parts.append(f'<div class="muted" style="color:#64748b;font-size:12.5px;margin-top:-2px;">Shape: {_escape(df.shape[0])} rows × {_escape(df.shape[1])} columns</div>')

    # KPI strip (only for dataframe)
    html_parts.append(_df_kpi_bar(df))

    # Detect score-like columns for spark bars
    lower_cols = {c.lower(): c for c in df.columns}
    spark_cols = set()
    for key in ["score", "q", "q_score", "q-score", "acc", "success", "sr", "reward"]:
        if key in lower_cols:
            spark_cols.add(lower_cols[key])

    # numeric min/max for spark normalization (per column)
    spark_stats = {}
    for c in spark_cols:
        s = pd.to_numeric(df[c], errors="coerce")
        vmin, vmax = float(s.min()), float(s.max())
        if math.isfinite(vmin) and math.isfinite(vmax) and vmax > vmin:
            spark_stats[c] = (vmin, vmax)
        else:
            spark_stats[c] = None

    # Build table manually (email-safe, precise control)
    html_parts.append('<table class="dataframe" role="table" cellspacing="0" cellpadding="0">')
    html_parts.append('<thead><tr>')
    html_parts.append('<th class="col-index"></th>')  # index column
    for c in df.columns:
        html_parts.append(f'<th>{_escape(c)}</th>')
    html_parts.append('</tr></thead>')

    html_parts.append('<tbody>')
    for idx, row in df.iterrows():
        html_parts.append('<tr>')
        html_parts.append(f'<td class="col-index">{_escape(idx)}</td>')

        for c in df.columns:
            v = row[c]
            is_num = pd.api.types.is_number(v) or (pd.api.types.is_numeric_dtype(df[c]) and v is not None)
            cls = "num" if is_num else ""
            display = _fmt_num(v, 3) if is_num else ("" if v is None else str(v))

            # spark bar for score-like cols
            if c in spark_cols:
                stat = spark_stats.get(c)
                pct = 0.0
                try:
                    fv = float(pd.to_numeric(v, errors="coerce"))
                    if stat is None:
                        # if no range, map [0,1] roughly
                        pct = max(0.0, min(1.0, fv))
                    else:
                        vmin, vmax = stat
                        pct = (fv - vmin) / (vmax - vmin) if vmax > vmin else 0.0
                        pct = max(0.0, min(1.0, pct))
                except Exception:
                    pct = 0.0

                html_parts.append(
                    f'<td class="{cls}">'
                    f'{_escape(display)}'
                    f'<div class="spark"><span style="width:{pct*100:.1f}%;"></span></div>'
                    f'</td>'
                )
            else:
                html_parts.append(f'<td class="{cls}">{_escape(display)}</td>')

        html_parts.append('</tr>')
    html_parts.append('</tbody></table>')
    html_parts.append('</div>')
    return "".join(html_parts)


def generate_html(data: Any, title: str = "Data Report") -> str:
    html_parts = []
    html_parts.append(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{_escape(title)}</title>
      <style>{_get_css()}</style>
    </head>
    <body>
      <div class="container">
        <header>
          <h1>{_escape(title)}</h1>
          <p class="timestamp">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        <main>
    """)

    if isinstance(data, pd.DataFrame):
        html_parts.append(_dataframe_to_html(data))
        html_parts.append('<div class="footer" style="text-align: center;">Generated by <a href="https://github.com/DelinQu/drop_email" target="_blank" rel="noopener noreferrer">Drop Email</a>🍻</div>')


    elif isinstance(data, dict):
        html_parts.append(_dict_to_html(data))
    elif isinstance(data, list):
        html_parts.append(_list_to_html(data))
    else:
        html_parts.append(_simple_value_to_html(data))

    html_parts.append("""
        </main>
      </div>
    </body>
    </html>
    """)
    return "\n".join(html_parts)


def _dict_to_html(data: Dict) -> str:
    """Convert dictionary to HTML."""
    html = '<div class="data-section">'
    html += '<h2>Dictionary</h2>'
    
    for key, value in data.items():
        html += '<div class="dict-item">'
        html += f'<span class="dict-key">{key}:</span>'
        
        if isinstance(value, (dict, list)):
            html += f'<div class="json-preview">{json.dumps(value, indent=2, ensure_ascii=False)}</div>'
        elif isinstance(value, pd.DataFrame):
            html += _dataframe_to_html(value)
        else:
            html += f'<span class="dict-value">{str(value)}</span>'
        
        html += '</div>'
    
    html += '</div>'
    return html


def _list_to_html(data: List) -> str:
    """Convert list to HTML."""
    html = '<div class="data-section">'
    html += f'<h2>List (Length: {len(data)})</h2>'
    
    # If list contains DataFrames, render them
    if data and isinstance(data[0], pd.DataFrame):
        for i, df in enumerate(data):
            html += f'<h3 style="margin-top: 20px; color: #667eea;">Item {i+1}</h3>'
            html += _dataframe_to_html(df)
    else:
        for i, item in enumerate(data):
            html += '<div class="list-item">'
            html += f'<strong>[{i}]</strong> '
            
            if isinstance(item, (dict, list)):
                html += f'<div class="json-preview">{json.dumps(item, indent=2, ensure_ascii=False)}</div>'
            elif isinstance(item, pd.DataFrame):
                html += _dataframe_to_html(item)
            else:
                html += f'<span>{str(item)}</span>'
            
            html += '</div>'
    
    html += '</div>'
    return html


def _simple_value_to_html(value: Any) -> str:
    """Convert simple value to HTML."""
    html = '<div class="data-section">'
    html += '<div class="simple-value">'
    html += f'<pre>{str(value)}</pre>'
    html += '</div>'
    html += '</div>'
    return html

