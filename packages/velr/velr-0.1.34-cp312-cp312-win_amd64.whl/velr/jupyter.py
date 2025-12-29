# velrpy/jupyter.py
from __future__ import annotations
import shlex, argparse, io, os
from typing import Optional, Dict, List
from IPython.core.magic import register_line_cell_magic
from IPython.display import display, HTML
from time import perf_counter

from .driver import Velr, VelrTx, VelrError
from .jupyter_render import render_table_html, ensure_css_once

def load_ipython_extension(ip):
    # Preload CSS so the very first render has styles
    ensure_css_once()

# --- Global notebook state ---
_DB_REG: Dict[str, Velr] = {}         # name -> Velr
_TX_REG: Dict[str, VelrTx] = {}       # name -> open tx (if any)
_CUR_DB: Optional[str] = None         # current/active name

def _ensure_db_name(name: Optional[str]) -> str:
    global _CUR_DB
    if name:
        return name
    if _CUR_DB:
        return _CUR_DB
    if len(_DB_REG) == 1:
        return next(iter(_DB_REG.keys()))
    return "default"

def _get_db(name: Optional[str] = None) -> Velr:
    nm = _ensure_db_name(name)
    db = _DB_REG.get(nm)
    if db is None:
        if nm == "default":
            db = Velr.open(None)
            _DB_REG[nm] = db
            global _CUR_DB
            _CUR_DB = nm
        else:
            raise VelrError(f"No DB named '{nm}'. Use %velr -open {nm} [PATH].")
    return db

def _set_current(name: str):
    global _CUR_DB
    if name not in _DB_REG:
        raise VelrError(f"No DB named '{name}'.")
    _CUR_DB = name

def _close_one(name: str):
    tx = _TX_REG.pop(name, None)
    if tx is not None:
        try: tx.rollback()
        except Exception: pass
        try: tx.close()
        except Exception: pass
    db = _DB_REG.pop(name, None)
    if db is not None:
        try: db.close()
        except Exception: pass
    global _CUR_DB
    if _CUR_DB == name:
        _CUR_DB = next(iter(_DB_REG.keys()), None)

def _close_all():
    for name in list(_DB_REG.keys()):
        _close_one(name)

def _fetch_last_table_for(cypher: str, *, dbname: str):
    """
    Execute `cypher` using active tx if any; return the *last* velr_table (or None).
    Caller is responsible for closing the returned table.
    """
    db = _get_db(dbname)
    tx = _TX_REG.get(dbname)

    def _stream():
        return (tx.exec if tx is not None else db.exec)(cypher)

    last_table = None
    with _stream() as st:
        while True:
            t = st.next_table()
            if t is None:
                break
            if last_table is not None:
                last_table.close()
            last_table = t
    return last_table

def _render_html_last(dbname: str, cypher: str, t0: float):
    tbl = _fetch_last_table_for(cypher, dbname=dbname)
    if tbl is None:
        elapsed_ms = (perf_counter() - t0) * 1000.0
        display(HTML(
            f"<i>No result tables on <b>{dbname}</b>. "
            f"Query executed in {elapsed_ms:.2f} ms</i>"
        ))
        return None

    headers = tbl.column_names()
    rows_py: List[list] = []
    with tbl.rows() as rows:
        for row in rows:
            rows_py.append([c.as_python(decode_text=True) for c in row])

    elapsed_ms = (perf_counter() - t0) * 1000.0
    render_table_html(
        headers, rows_py,
        footer=f"DB: {dbname} • Query executed in {elapsed_ms:.2f} ms"
    )
    tbl.close()
    return None  # HTML path just displays

def _as_pandas(dbname: str, cypher: str):
    tbl = _fetch_last_table_for(cypher, dbname=dbname)
    if tbl is None:
        try:
            import pandas as pd  # type: ignore
            return pd.DataFrame()
        except Exception:
            raise VelrError("No result tables and pandas is not installed.")
    try:
        return tbl.to_pandas()
    finally:
        tbl.close()

def _as_polars(dbname: str, cypher: str):
    tbl = _fetch_last_table_for(cypher, dbname=dbname)
    if tbl is None:
        try:
            import polars as pl  # type: ignore
            return pl.DataFrame()
        except Exception:
            raise VelrError("No result tables and polars is not installed.")
    try:
        return tbl.to_polars()
    finally:
        tbl.close()

def _as_pyarrow(dbname: str, cypher: str):
    tbl = _fetch_last_table_for(cypher, dbname=dbname)
    if tbl is None:
        import pyarrow as pa  # type: ignore
        return pa.table({})
    try:
        return tbl.to_pyarrow()
    finally:
        tbl.close()

def _default_arrow_filename(path: str | None) -> str:
    """Pick a sensible default and extension (.arrow) if missing."""
    if not path:
        return "result.arrow"
    base = path
    # If path ends with a directory separator, write result.arrow inside it
    if base.endswith(os.sep):
        return os.path.join(base, "result.arrow")
    # If no extension, add .arrow
    root, ext = os.path.splitext(base)
    if not ext:
        return base + ".arrow"
    return base

def _save_arrow_file(dbname: str, cypher: str, path: str) -> int:
    """
    Save last result table's Arrow IPC **file** (Feather v2) bytes to `path`.
    Returns number of bytes written.
    """
    tbl = _fetch_last_table_for(cypher, dbname=dbname)
    if tbl is None:
        raise VelrError("No result tables to save.")
    try:
        mv = tbl.to_ipc_memoryview()  # zero-copy memoryview
        out_path = _default_arrow_filename(path)
        # Ensure parent dir exists when a dir component is present
        d = os.path.dirname(out_path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        with open(out_path, "wb") as f:
            n = f.write(mv)
        return n
    finally:
        tbl.close()

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="%velr", add_help=False)
    modes = p.add_mutually_exclusive_group()
    modes.add_argument("-open", nargs="+", metavar=("NAME", "PATH"),
                       help="Open DB as NAME; PATH optional (in-memory if omitted)")
    modes.add_argument("-close", nargs="?", const="__CURRENT__", metavar="NAME|all",
                       help="Close a DB by NAME (or 'all'). No arg closes current.")
    modes.add_argument("-use", metavar="NAME", help="Set current DB name")
    modes.add_argument("-list", action="store_true", help="List open DBs")
    modes.add_argument("-tx", metavar="ACTION", choices=("begin","commit","rollback"),
                       help="Transaction: begin|commit|rollback")

    # Output mode & capture
    p.add_argument("-as", dest="as_kind",
                   choices=("html","pandas","polars","pyarrow","arrow-file","ipc-save"),  # ipc-save kept for compat
                   default="html",
                   help="How to present the LAST result table (default: html)")
    p.add_argument("-o", dest="out_var", metavar="VARNAME",
                   help="Store the result object (pandas/polars/pyarrow) in a variable")
    # New flag name
    p.add_argument("--out", dest="out_path", metavar="PATH",
                   help="When -as arrow-file, write Arrow IPC file (Feather v2) to PATH")
    # Old flag kept for compatibility; we’ll translate it
    p.add_argument("--save-ipc", dest="save_ipc", metavar="PATH",
                   help=argparse.SUPPRESS)

    # Common options
    p.add_argument("-db", metavar="NAME", help="Target DB name for this command/query")
    p.add_argument("-source", metavar="FILE", help="Run query from file")
    p.add_argument("-h", "--help", action="store_true", help="Show help")
    return p

def _fmt_list() -> str:
    if not _DB_REG:
        return "<i>No open databases.</i>"
    rows = []
    for nm in sorted(_DB_REG.keys()):
        tag = " (current)" if nm == _CUR_DB else ""
        tx = " [tx]" if nm in _TX_REG else ""
        rows.append(f"• <b>{nm}</b>{tag}{tx}")
    return "<div>" + "<br>".join(rows) + "</div>"

@register_line_cell_magic
def velr(line: str, cell: str | None = None):
    """
    %velr -open NAME [PATH]        # open file DB or in-memory if PATH omitted
    %velr -use NAME                # set current DB
    %velr -list                    # list open DBs (current marked)
    %velr -close [NAME|all]        # close DB by name (or all); no arg closes current
    %velr -tx begin|commit|rollback [-db NAME]
    %velr [-db NAME] [-as html|pandas|polars|pyarrow|arrow-file] [-o VAR] [--out PATH] [-source FILE] [inline cypher]
    %%velr [-db NAME] [-as ...] [-o VAR]
    <cypher in cell>

    Examples:
      %velr -open demo  ./mydb.velr
      %velr -use demo
      %velr -list

      # Pretty HTML preview (default)
      %%velr
      MATCH (s:Sample) RETURN s.i, s.b;

      # Pandas DataFrame and capture to df
      %%velr -as pandas -o df
      MATCH (s:Sample) RETURN s.i, s.b;

      # Polars
      %velr -as polars -o pl_df MATCH (s:Sample) RETURN s.i, s.b;

      # PyArrow Table
      %velr -as pyarrow -o pa_tbl MATCH (s:Sample) RETURN s.i, s.b;

      # Save as Arrow IPC file (Feather v2)
      %velr -as arrow-file --out /tmp/out.arrow MATCH (s:Sample) RETURN s.i, s.b;
    """
    ensure_css_once()
    try:
        args, extra = _parser().parse_known_args(shlex.split(line))
    except SystemExit:
        return

    if args.help:
        display(HTML(f"<pre>{velr.__doc__}</pre>")); return

    # Back-compat: translate old ipc-save flag/choice
    if args.as_kind == "ipc-save":
        display(HTML("<i>Note: <b>-as ipc-save</b> is deprecated. Use <b>-as arrow-file</b> instead.</i>"))
        args.as_kind = "arrow-file"
        # Prefer --out, but fall back to old --save-ipc if provided
        if not args.out_path and args.save_ipc:
            args.out_path = args.save_ipc

    # Open
    if args.open is not None:
        if len(args.open) == 0:
            display(HTML("<i>Usage: %velr -open NAME [PATH]</i>")); return
        name = args.open[0]
        path = None
        if len(args.open) > 1:
            path = " ".join(args.open[1:]).strip() or None

        if name in _DB_REG:
            _close_one(name)  # replace
        db = Velr.open(path)
        _DB_REG[name] = db
        _set_current(name)
        msg = f"Opened DB <b>{name}</b> at: {path}" if path else f"Opened in-memory DB as <b>{name}</b>"
        display(HTML(f"<i>{msg}</i>"))
        return

    # Use
    if args.use:
        try:
            _set_current(args.use)
            display(HTML(f"<i>Current DB: <b>{args.use}</b></i>"))
        except VelrError as e:
            display(HTML(f'<div style="color:#b91c1c">{e}</div>'))
        return

    # List
    if args.list:
        display(HTML(_fmt_list()))
        return

    # Close
    if args.close is not None:
        target = args.close
        if target == "all":
            _close_all()
            display(HTML("<i>Closed all DBs.</i>"))
            return
        if target == "__CURRENT__":
            if _CUR_DB is None:
                display(HTML("<i>No current DB.</i>")); return
            target = _CUR_DB
        if target not in _DB_REG:
            display(HTML(f"<i>No DB named '{target}'.</i>")); return
        _close_one(target)
        display(HTML(f"<i>Closed DB '{target}'.</i>"))
        return

    # Query resolution
    cypher = None
    if args.source:
        try:
            with io.open(args.source, "r", encoding="utf-8") as f:
                cypher = f.read()
        except Exception as e:
            display(HTML(f'<div style="color:#b91c1c">Could not read file: {e}</div>')); return
    elif cell is not None and cell.strip():
        cypher = cell
    else:
        cypher = " ".join(extra).strip() if extra else None

    if not cypher:
        display(HTML("<i>No query provided. Use inline text, a cell body, or -source FILE.</i>"))
        return

    # Execute with chosen output mode
    dbname = _ensure_db_name(args.db)
    t0 = perf_counter()
    try:
        kind = args.as_kind
        if kind == "html":
            _ = _render_html_last(dbname, cypher, t0)
            return

        if kind == "pandas":
            obj = _as_pandas(dbname, cypher)
        elif kind == "polars":
            obj = _as_polars(dbname, cypher)
        elif kind == "pyarrow":
            obj = _as_pyarrow(dbname, cypher)
        elif kind == "arrow-file":
            path = args.out_path or "result.arrow"
            n = _save_arrow_file(dbname, cypher, path)
            display(HTML(f"<i>Saved Arrow IPC file (Feather v2) to <b>{_default_arrow_filename(path)}</b> ({n} bytes)</i>"))
            return
        else:
            display(HTML("<i>Unknown -as mode.</i>")); return

        # Store or display the object
        if args.out_var:
            get_ipython().user_ns[args.out_var] = obj
            display(HTML(f"<i>Stored result in <b>{args.out_var}</b></i>"))
        else:
            display(obj)

    except VelrError as e:
        display(HTML(f'<div style="color:#b91c1c">VelrError: {e}</div>'))

def unload_ipython_extension(ip):
    _close_all()
