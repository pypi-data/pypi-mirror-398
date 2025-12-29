# velrpy/jupyter_render.py
from html import escape
from IPython.display import HTML, display

# Injected once per kernel
__VELR_CSS_INJECTED = False

_VELR_CSS = """
<style id="velrpy-css">
/* Outer scroller only (no borders/rounded corners) */
.velrpy-wrap {
  max-height: 420px;
  overflow: auto;
  overflow-x: auto;
}

/* Natural widths; compact look; inherit notebook theme colors */
.velrpy-table {
  border-collapse: collapse;
  border: none;
  width: auto;
  max-width: 100%;
  table-layout: auto;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

.velrpy-table thead th,
.velrpy-table tbody td {
  font-size: 12px;
  padding: 6px 8px;
  vertical-align: top;
  white-space: nowrap; /* avoid huge wrapped cells by default */
}

/* Sticky header with centered text */
.velrpy-table thead th {
  position: sticky;
  top: 0;
  background: transparent;
  z-index: 1;
  font-weight: 600;
  text-align: center;                 /* ⟵ center all headers */
  color: inherit;
  border-bottom: 1px solid rgba(127,127,127,.35);
}



/* Body rows: thin dividers; inherit theme */
.velrpy-table tbody td {
  color: inherit;
  border-bottom: 1px solid rgba(127,127,127,.18);
}

/* Alignment helpers */
.velrpy-table td.num  { text-align: right;  font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
.velrpy-table td.bool { text-align: center; }

.velrpy-table thead th.num  { text-align: right; }
.velrpy-table thead th.bool { text-align: center; }

/* Null styling */
.velrpy-table .null { opacity: .7; font-style: italic; }

/* Footer */
.velrpy-foot { margin-top: 6px; opacity: .7; font-size: 11px; }

/* Guard */
.velrpy-table tbody { visibility: visible; }
</style>
"""

def ensure_css_once() -> bool:
    """
    Inject the CSS exactly once per kernel. Returns True if injected this call,
    False if it was already present.
    """
    global __VELR_CSS_INJECTED
    if not __VELR_CSS_INJECTED:
        display(HTML(_VELR_CSS))
        __VELR_CSS_INJECTED = True
        return True
    return False

# Back-compat alias
def _ensure_css_once():
    ensure_css_once()

def _is_bool(x):
    return isinstance(x, bool)

def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _fmt_cell(v, decode_json_preview=False, max_len=200):
    if v is None:
        return '<span class="null">NULL</span>'
    # bytes -> utf-8 best-effort
    if isinstance(v, (bytes, bytearray)):
        try:
            v = v.decode("utf-8")
        except Exception:
            v = v.hex()
    s = str(v)

    # Optional: tiny JSON preview (hook kept for future)
    if decode_json_preview and s and (s.startswith("{") or s.startswith("[")):
        pass

    if len(s) > max_len:
        s = escape(s[: max_len - 1]) + "…"
    else:
        s = escape(s)
    return s

def render_table_html(headers, rows, *, footer=None, shown=None, total=None):
    # Ensure stylesheet present
    try:
        ensure_css_once()
    except Exception:
        pass

    # Build header (class not needed anymore; CSS centers all th)
    thead = "".join(f"<th>{escape(h)}</th>" for h in headers)

    # Build body rows (keep numeric/bool alignment)
    body_rows = []
    for r in rows:
        tds = []
        for v in r:
            cls = "num" if _is_num(v) else ("bool" if _is_bool(v) else "")
            tds.append(f'<td class="{cls}">{_fmt_cell(v)}</td>')
        body_rows.append("<tr>" + "".join(tds) + "</tr>")
    tbody = "\n".join(body_rows)

    # Footer
    foot_bits = []
    if shown is not None and total is not None:
        foot_bits.append(f"Showing {shown} of {total} row(s)")
    if footer:
        foot_bits.append(escape(footer))
    foot_html = f'<div class="velrpy-foot">{" • ".join(foot_bits)}</div>' if foot_bits else ""

    # Inline fallback (in case <style> is ignored) — note center for th here too
    wrap_style  = "max-height:420px;overflow:auto;overflow-x:auto;"
    table_style = (
        "border-collapse:collapse;border:none;width:auto;max-width:100%;table-layout:auto;"
        "color:inherit;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
    )
    th_style    = (
        "position:sticky;top:0;background:transparent;z-index:1;font-weight:600;"
        "border-bottom:1px solid rgba(127,127,127,.35);padding:6px 8px;text-align:center;"  # ← center
        "font-size:12px;color:inherit;white-space:nowrap;"
    )
    td_style    = (
        "padding:6px 8px;border-bottom:1px solid rgba(127,127,127,.18);"
        "font-size:12px;color:inherit;vertical-align:top;white-space:nowrap;"
    )

    html = f"""
<div class="velrpy-wrap" style="{wrap_style}">
  <table class="velrpy-table" style="{table_style}">
    <thead><tr>{"".join(f'<th style="{th_style}">{escape(h)}</th>' for h in headers)}</tr></thead>
    <tbody>
      {tbody.replace('<td class="', f'<td style="{td_style}" class="')}
    </tbody>
  </table>
</div>
{foot_html}
"""
    display(HTML(html))
