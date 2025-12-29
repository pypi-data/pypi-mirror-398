# src/velrpy/driver.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple
import weakref
import sys

from ._ffi import ffi, lib


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Helps type checkers without forcing a runtime import
    import pyarrow as pa # type: ignore[import-not-found]
    import pandas as pd # type: ignore[import-not-found]
    import polars as pl # type: ignore[import-not-found]

# ---- Foreign IPC buffer (zero-copy holder) ----
# ---- Foreign IPC buffer (zero-copy holder) ----


def _normalize_arrow_columns(cols_like):
    """
    Accepts:
      - Mapping[str, pa.Array | pa.ChunkedArray]
      - Sequence[tuple[str, pa.Array | pa.ChunkedArray]]
      - pyarrow.RecordBatch  (columns are pa.Array)
      - pyarrow.Table        (columns are pa.ChunkedArray)
    Returns: list[(name:str, arr_or_chunked: Union[pa.Array, pa.ChunkedArray])]
    """
    import pyarrow as pa  # type: ignore

    # mapping
    if hasattr(cols_like, "items"):
        items = list(cols_like.items())
        for k, v in items:
            if not isinstance(v, (pa.Array, pa.ChunkedArray)):
                raise VelrError(f"Column '{k}' must be a pyarrow.Array or ChunkedArray")
        return items

    # sequence of pairs
    if isinstance(cols_like, (list, tuple)) and cols_like and isinstance(cols_like[0], (list, tuple)):
        out = []
        for k, v in cols_like:
            if not isinstance(v, (pa.Array, pa.ChunkedArray)):
                raise VelrError(f"Column '{k}' must be a pyarrow.Array or ChunkedArray")
            out.append((k, v))
        return out

    # RecordBatch -> Arrays
    if isinstance(cols_like, pa.RecordBatch):
        return [(f.name, cols_like.column(i)) for i, f in enumerate(cols_like.schema)]

    # Table -> ChunkedArray per column (no combining; chunked path handles it)
    if isinstance(cols_like, pa.Table):
        return [(n, cols_like[n]) for n in cols_like.schema.names]

    raise VelrError("Unsupported columns object; pass {name: pa.Array|pa.ChunkedArray}, "
                    "list[(name, pa.Array|pa.ChunkedArray)], pyarrow.RecordBatch, or pyarrow.Table")


def _pandas_to_arrow_table(
    df: "pd.DataFrame",
    *,
    index: bool = False,
    jsonify_objects: bool = True,
    schema: "Optional[pa.Schema]" = None,
):
    """
    Convert a pandas.DataFrame to a pyarrow.Table with defaults that play nicely
    with the velr Arrow binder.

    - index=False by default (don’t include the pandas index as a column).
    - jsonify_objects=True serializes object-dtype cells that are list/dict/tuple/set
      as JSON strings; other non-JSONable scalars become str(...). None stays None.
      This avoids awkward Arrow types that the driver may not support yet.
    - You can pass a pyarrow.Schema to control dtypes explicitly.
    """
    import math
    import json
    import pandas as pd  # type: ignore
    import pyarrow as pa  # type: ignore

    work = df.copy(deep=False)

    # Coerce column names to strings (Arrow + engine expect str column names)
    if any(not isinstance(c, str) for c in work.columns):
        work.columns = [str(c) for c in work.columns]

    if jsonify_objects:
        from pandas.api import types as ptypes

        def _jsonify_series(s: "pd.Series") -> "pd.Series":
            # Keep None/NaN as None; JSONify containers; fallback to str for scalars
            def _coerce(x):
                if x is None or (isinstance(x, float) and math.isnan(x)):
                    return None
                if isinstance(x, (dict, list, tuple, set)):
                    if isinstance(x, set):
                        x = list(x)  # sets aren’t JSON-serializable; make a list
                    return json.dumps(x, ensure_ascii=False)
                # strings: keep as-is to avoid double quoting
                if isinstance(x, str):
                    return x
                # numbers/bools: keep as-is so Arrow infers numeric/bool if column is uniform
                if isinstance(x, (bool, int, float)):
                    return x
                # everything else -> string
                return str(x)

            return s.map(_coerce)

        for name in work.columns:
            s = work[name]
            if ptypes.is_object_dtype(s.dtype):
                work[name] = _jsonify_series(s)

        # Prefer stable/explicit dtypes to help Arrow inference
        for name in work.columns:
            s = work[name]
            if ptypes.is_bool_dtype(s.dtype):
                # leave bools
                continue
            if ptypes.is_integer_dtype(s.dtype):
                # use pandas nullable Int64 to preserve nulls cleanly
                try:
                    work[name] = s.astype("Int64")
                except Exception:
                    pass
            elif ptypes.is_float_dtype(s.dtype):
                # ensure float64
                work[name] = s.astype("float64")
            elif ptypes.is_string_dtype(s.dtype):
                # ensure pandas string dtype (optional)
                try:
                    work[name] = s.astype("string[python]")
                except Exception:
                    pass

    # Build Arrow table
    return pa.Table.from_pandas(work, schema=schema, preserve_index=index)


def _polars_to_arrow_table(df: "pl.DataFrame", *, rechunk: bool = False):
    """
    Convert a polars.DataFrame to a pyarrow.Table.
    - rechunk=True to consolidate into contiguous buffers (nice for zero-copy).
    """
    import pyarrow as pa  # type: ignore
    import polars as pl  # type: ignore

    if rechunk:
        df = df.rechunk()
    # Polars gives a pyarrow.Table directly; column names are already strings.
    return df.to_arrow()



def _numpy_to_arrow_table(data, *, names: list[str] | None = None, types: dict | None = None):
    """
    NumPy dict/2D array → pyarrow.Table
    Accepts:
      - dict[str, np.ndarray]
      - 2D np.ndarray + names=[...]
    """
    import numpy as np   # type: ignore
    import pyarrow as pa # type: ignore

    if isinstance(data, dict):
        cols = {}
        for name, arr in data.items():
            # pa.array(np.ndarray) is zero-copy for many numeric dtypes
            dt = types.get(name) if types else None
            cols[name] = pa.array(arr, type=dt) if dt is not None else pa.array(arr)
        return pa.table(cols)

    if isinstance(data, np.ndarray):
        if data.ndim != 2:
            raise VelrError("2D numpy.ndarray expected when passing a bare array")
        if not names:
            raise VelrError("You must supply 'names=[...]' for a 2D numpy array")
        if data.shape[1] != len(names):
            raise VelrError("len(names) must equal array.shape[1]")
        cols = {}
        for i, name in enumerate(names):
            col = data[:, i]
            dt = types.get(name) if types else None
            cols[name] = pa.array(col, type=dt) if dt is not None else pa.array(col)
        return pa.table(cols)

    raise VelrError("Unsupported NumPy input; pass dict[str, ndarray] or a 2D ndarray with names=[]")


def _records_to_arrow_table(rows, *, types: dict | None = None):
    """
    List[dict] → pyarrow.Table
    """
    import pyarrow as pa  # type: ignore
    schema = (pa.schema([pa.field(n, t) for n, t in types.items()])
              if types else None)
    # from_pylist respects schema if provided; otherwise infers
    tbl = pa.Table.from_pylist(rows, schema=schema)
    return tbl


def _export_arrow_columns_for_bind(pairs):
    """
    Given list[(name:str, arr:pa.Array)], build:
      - schemas_pp: const ArrowSchema*[]
      - arrays_pp:  const ArrowArray*[]
      - name_views: velr_strview[] (and keep the backing byte buffers alive)
    Uses pyarrow.cffi.ffi to allocate Arrow C structs, exports via _export_to_c,
    then casts their addresses into our cffi world.
    """
    import pyarrow as pa  # type: ignore
    from pyarrow.cffi import ffi as paffi  # authoritative Arrow C ABI FFI

    n = len(pairs)
    # These two hold the actual C Arrow structs (must stay alive until we return)
    c_schemas = [paffi.new("struct ArrowSchema*") for _ in range(n)]
    c_arrays  = [paffi.new("struct ArrowArray*")  for _ in range(n)]

    # Export both array + schema per column
    for i, (name, arr) in enumerate(pairs):
        if not isinstance(arr, pa.Array):
            raise VelrError(f"Column '{name}' is not a pyarrow.Array")
        ptr_schema = int(paffi.cast("uintptr_t", c_schemas[i]))
        ptr_array  = int(paffi.cast("uintptr_t", c_arrays[i]))
        # one call exports both the ArrowArray and ArrowSchema
        arr._export_to_c(ptr_array, ptr_schema)

    # Build our pointer arrays using *our* cffi 'ffi'
    schemas_pp = ffi.new("const struct ArrowSchema * []", n)
    arrays_pp  = ffi.new("const struct ArrowArray  * []", n)
    for i in range(n):
        schemas_pp[i] = ffi.cast("const struct ArrowSchema *",
                                 int(paffi.cast("uintptr_t", c_schemas[i])))
        arrays_pp[i]  = ffi.cast("const struct ArrowArray *",
                                 int(paffi.cast("uintptr_t", c_arrays[i])))

    # Build velr_strview[]; keep backing buffers alive in a list
    name_views = ffi.new("velr_strview[]", n)
    name_backing = []  # keep refs so GC can't free before the bind call
    for i, (name, _) in enumerate(pairs):
        b = name.encode("utf-8", "strict")
        buf = ffi.new("unsigned char[]", b)
        name_backing.append(buf)
        name_views[i].ptr = buf
        name_views[i].len = len(b)

    return schemas_pp, arrays_pp, name_views, name_backing, c_schemas, c_arrays

def _export_arrow_columns_for_bind_chunked(pairs):
    """
    Build per-column velr_arrow_chunks[]:
      - For each column i:
          schemas[i] -> const ArrowSchema* [chunk_count_i]
          arrays[i]  -> const ArrowArray*  [chunk_count_i]
          chunk_count_i
      - name_views -> velr_strview[col_count]
    Keeps all needed Python-side objects alive for the duration of the call.

    Returns:
      (cols_c, name_views,
       name_backing, keep_schemas_nested, keep_arrays_nested,
       schema_pp_per_col, array_pp_per_col)
    """
    import pyarrow as pa  # type: ignore
    from pyarrow.cffi import ffi as paffi  # authoritative Arrow C Data FFI

    col_count = len(pairs)

    # Gather chunks per column
    per_col_chunks = []
    for _, arr in pairs:
        if isinstance(arr, pa.ChunkedArray):
            chunks = list(arr.chunks)
        elif isinstance(arr, pa.Array):
            chunks = [arr]
        else:
            raise VelrError("Expected pa.Array or pa.ChunkedArray")
        if not chunks:
            raise VelrError("ChunkedArray has zero chunks")
        per_col_chunks.append(chunks)

    # For each (col, chunk), allocate ArrowSchema*/ArrowArray* via PyArrow
    keep_schemas_nested = []  # shape: [ [pa_ffi ArrowSchema* ...], ... ]
    keep_arrays_nested  = []  # shape: [ [pa_ffi ArrowArray*  ...], ... ]
    schema_pp_per_col   = []  # our cffi "const ArrowSchema* []" per column
    array_pp_per_col    = []  # our cffi "const ArrowArray*  []" per column

    for chunks in per_col_chunks:
        n = len(chunks)

        # allocate pyarrow-side holders
        ks = [paffi.new("struct ArrowSchema*") for _ in range(n)]
        ka = [paffi.new("struct ArrowArray*")  for _ in range(n)]

        # allocate our cffi pointer arrays for this column
        schemas_pp = ffi.new("const struct ArrowSchema * []", n)
        arrays_pp  = ffi.new("const struct ArrowArray  * []", n)

        for j, ch in enumerate(chunks):
            # Export Arrow C Data for this chunk
            ptr_schema = int(paffi.cast("uintptr_t", ks[j]))
            ptr_array  = int(paffi.cast("uintptr_t", ka[j]))
            ch._export_to_c(ptr_array, ptr_schema)

            # Cast the pyarrow-owned C pointers into our cffi world
            schemas_pp[j] = ffi.cast(
                "const struct ArrowSchema *",
                int(paffi.cast("uintptr_t", ks[j]))
            )
            arrays_pp[j] = ffi.cast(
                "const struct ArrowArray *",
                int(paffi.cast("uintptr_t", ka[j]))
            )

        keep_schemas_nested.append(ks)
        keep_arrays_nested.append(ka)
        schema_pp_per_col.append(schemas_pp)
        array_pp_per_col.append(arrays_pp)

    # Build velr_arrow_chunks[col_count]
    cols_c = ffi.new("struct velr_arrow_chunks[]", col_count)
    for i, chunks in enumerate(per_col_chunks):
        cols_c[i].schemas = schema_pp_per_col[i]
        cols_c[i].arrays  = array_pp_per_col[i]
        cols_c[i].chunk_count = len(chunks)

    # Build velr_strview[col_count] for column names + keep their buffers
    name_views = ffi.new("velr_strview[]", col_count)
    name_backing = []
    for i, (name, _) in enumerate(pairs):
        b = name.encode("utf-8", "strict")
        buf = ffi.new("unsigned char[]", b)
        name_backing.append(buf)
        name_views[i].ptr = buf
        name_views[i].len = len(b)

    return (cols_c, name_views,
            name_backing, keep_schemas_nested, keep_arrays_nested,
            schema_pp_per_col, array_pp_per_col)



class _ForeignIPC:
    """
    Owns an Arrow IPC file buffer allocated by Rust. Memory is freed automatically
    when this object (or any pyarrow buffers created from it) are GC'd.
    """
    __slots__ = ("_cdata", "_len", "_mv", "_finalized")

    def __init__(self, ptr, length: int):
        n = int(length)
        self._len = n

        if ptr == ffi.NULL or n == 0:
            self._cdata = ffi.NULL
            self._mv = memoryview(b"")
            return

        raw = ffi.cast("unsigned char *", ptr)

        # finalizer without closing over `self`
        def _finalize(p):
            if p != ffi.NULL and n >= 0:
                lib.velr_free(p, n)

        self._cdata = ffi.gc(raw, _finalize)
        self._mv = memoryview(ffi.buffer(self._cdata, n))

    def memoryview(self) -> memoryview:
        return self._mv

    def to_buffer(self):
        """Return a pyarrow.Buffer that views the same memory (zero-copy)."""
        try:
            import pyarrow as pa  # type: ignore[import-not-found]
        except Exception as e:
            raise VelrError(f"pyarrow is required for zero-copy buffer: {e}") from e
        return pa.py_buffer(self._mv)

    def to_pyarrow(self):
        """Decode IPC file → pa.Table (still zero-copy under the hood)."""
        try:
            import pyarrow as pa  # type: ignore[import-not-found]
        except Exception as e:
            raise VelrError(f"pyarrow is required: {e}") from e
        buf = self.to_buffer()
        with pa.BufferReader(buf) as reader:
            return pa.ipc.open_file(reader).read_all()

    def to_pandas(self, *, dtype_backend: str = "numpy_nullable", **kwargs):
            """
            Decode IPC file → pa.Table → pandas.DataFrame.

            - We keep Arrow → pandas conversion simple (no Arrow-specific kwargs).
            - Then we let pandas handle nullable dtypes via convert_dtypes().
            """
            tbl = self.to_pyarrow()
            try:
                import pandas as pd  # type: ignore[import-not-found]
            except Exception as e:
                raise VelrError(f"pandas is required for to_pandas(): {e}") from e

            # First do the plain Arrow -> pandas conversion
            df = tbl.to_pandas()  # no use_nullable_dtypes; works on old & new pyarrow

            # Then upgrade dtypes on the pandas side
            # If caller explicitly passed dtype_backend in **kwargs, respect that.
            backend = kwargs.pop("dtype_backend", dtype_backend)
            if backend is not None:
                try:
                    df = df.convert_dtypes(dtype_backend=backend)
                except TypeError:
                    # Older pandas without dtype_backend support: fall back to classic convert_dtypes
                    df = df.convert_dtypes()

            # Any remaining kwargs are unexpected here; either ignore or raise.
            if kwargs:
                # optional: raise to surface misuse
                raise VelrError(f"Unsupported to_pandas() kwargs: {list(kwargs.keys())}")

            return df

    def to_polars(self):
        try:
            import polars as pl  # type: ignore[import-not-found]
        except Exception as e:
            raise VelrError(f"polars is required for to_polars(): {e}") from e
        # Construct from Arrow table (generally zero-copy)
        return pl.from_arrow(self.to_pyarrow())

    def raw_memoryview(self) -> memoryview:
        return self._mv

    def to_bytes(self) -> bytes:
        return bytes(self._mv)

    def write_to(self, fileobj) -> int:
        return fileobj.write(self._mv)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            f.write(self._mv)


class VelrError(RuntimeError): pass

def _take_err(errpp) -> str:
    if errpp[0] == ffi.NULL:
        return "(unknown)"
    s = ffi.string(errpp[0]).decode("utf-8", errors="replace")
    lib.velr_string_free(errpp[0])
    errpp[0] = ffi.NULL
    return s

def _check(rc: int, errpp) -> None:
    if rc != lib.VELR_OK:
        raise VelrError(_take_err(errpp))

@dataclass(frozen=True)
class Cell:
    ty: int
    i64: int
    f64: float
    data: bytes
    def as_python(self, *, decode_text=True, parse_json=False,
                  encoding="utf-8", errors="strict"):
        if self.ty == lib.VELR_NULL:   return None
        if self.ty == lib.VELR_BOOL:   return bool(self.i64)
        if self.ty == lib.VELR_INT64:  return int(self.i64)
        if self.ty == lib.VELR_DOUBLE: return float(self.f64)
        if self.ty == lib.VELR_TEXT:
            return self.data.decode(encoding, errors) if decode_text else bytes(self.data)
        if self.ty == lib.VELR_JSON:
            if parse_json:
                import json
                return json.loads(self.data.decode(encoding, errors))
            return self.data.decode(encoding, errors) if decode_text else bytes(self.data)
        return bytes(self.data)

# ================= Velr (connection) =================

class Velr:
    __slots__ = ("_db",)
    def __init__(self, db_cdata):
        self._db = db_cdata

    @classmethod
    def open(cls, path: Optional[str]=None) -> "Velr":
        out_db = ffi.new("velr_db **")
        out_err = ffi.new("char **")
        rc = lib.velr_open(path.encode() if path is not None else ffi.NULL, out_db, out_err)
        _check(rc, out_err)
        return cls(out_db[0])

    def close(self) -> None:
        if self._db != ffi.NULL:
            lib.velr_close(self._db)
            self._db = ffi.NULL

    def __enter__(self) -> "Velr": return self
    def __exit__(self, exc_type, exc, tb): self.close()

    def run(self, cypher: str) -> None:
        """Execute and drain all result tables (for DDL/DML or scripts)."""
        with self.exec(cypher) as st:
            while True:
                t = st.next_table()
                if t is None:
                    break
                t.close()

    def execute(self, cypher: str) -> None:
        """Alias for run(); DB-API-ish name."""
        return self.run(cypher)

    # -------- OUTSIDE TX --------
    def exec(self, cypher: str) -> "Stream":
        out_st = ffi.new("velr_stream **")
        out_err = ffi.new("char **")
        rc = lib.velr_exec_start(self._db, cypher.encode(), out_st, out_err)
        _check(rc, out_err)
        return Stream(out_st[0])

        # OPTIONAL: keep the native fast-path private for future toggles/benchmarks
    def _exec_one_native(self, cypher: str) -> "Table":
        out_tbl = ffi.new("velr_table **")
        out_err = ffi.new("char **")
        rc = lib.velr_exec_one(self._db, cypher.encode(), out_tbl, out_err)
        _check(rc, out_err)
        return Table(out_tbl[0])
    
    def exec_one(self, cypher: str) -> "Table":
        """Expect exactly one table; raises if none or more than one."""
        with self.exec(cypher) as st:
            t1 = st.next_table()
            if t1 is None:
                raise VelrError("query produced no result tables")
            t2 = st.next_table()
            if t2 is not None:
                # Clean up and error
                try: t2.close()
                except Exception: pass
                try: t1.close()
                except Exception: pass
                raise VelrError("query produced multiple tables; use exec() to stream them")
            return t1  # caller closes
    
    def to_pyarrow(self, cypher: str):
        """Return pyarrow.Table of the LAST result table and drain the rest."""
        with self.exec(cypher) as st:
            last = None
            while True:
                t = st.next_table()
                if t is None:
                    break
                if last is not None:
                    last.close()
                last = t
            if last is None:
                import pyarrow as pa
                import pyarrow as pa  # no result: return empty table with no schema
                return pa.table({})
            try:
                return last.to_pyarrow()
            finally:
                last.close()

    def to_pandas(self, cypher: str, **kwargs):
        pa_tbl = self.to_pyarrow(cypher)
        # Mirror the same semantics as _ForeignIPC.to_pandas
        import pandas as pd  # type: ignore[import-not-found]
        df = pa_tbl.to_pandas()
        backend = kwargs.pop("dtype_backend", "numpy_nullable")
        if backend is not None:
            try:
                df = df.convert_dtypes(dtype_backend=backend)
            except TypeError:
                df = df.convert_dtypes()
        if kwargs:
            raise VelrError(f"Unsupported to_pandas() kwargs: {list(kwargs.keys())}")
        return df

    def to_polars(self, cypher: str):
        import polars as pl
        return pl.from_arrow(self.to_pyarrow(cypher))
    
    def bind_arrow(self, logical: str, columns) -> None:
        pairs = _normalize_arrow_columns(columns)
        (cols_c, name_views,
        _name_backing, _keep_schemas_nested, _keep_arrays_nested,
        _schema_pp_per_col, _array_pp_per_col) = _export_arrow_columns_for_bind_chunked(pairs)

        out_err = ffi.new("char **")
        logical_c = ffi.new("char[]", logical.encode("utf-8"))
        rc = lib.velr_bind_arrow_chunks(
            self._db,
            logical_c,
            cols_c,
            name_views,
            len(pairs),
            out_err,
        )
        _check(rc, out_err)

    def bind_pandas(
        self,
        logical: str,
        df: "pd.DataFrame",
        *,
        index: bool = False,
        jsonify_objects: bool = True,
        schema: "Optional['pa.Schema']" = None,
    ) -> None:
        """
        Bind a pandas DataFrame as a logical table.
        Defaults:
          - index=False (don’t include the pandas index)
          - jsonify_objects=True (object columns with lists/dicts -> JSON text)
        """
        tbl = _pandas_to_arrow_table(df, index=index, jsonify_objects=jsonify_objects, schema=schema)
        # `bind_arrow` accepts a pyarrow.Table directly
        self.bind_arrow(logical, tbl)

    def bind_polars(
        self,
        logical: str,
        df: "pl.DataFrame",
        *,
        rechunk: bool = False,
    ) -> None:
        """
        Bind a polars DataFrame as a logical table.
        Defaults:
          - rechunk=True (consolidate buffers)
        """
        tbl = _polars_to_arrow_table(df, rechunk=rechunk)
        self.bind_arrow(logical, tbl)

    def bind_numpy(
        self,
        logical: str,
        data,
        *,
        names: list[str] | None = None,
        types: dict | None = None,
    ) -> None:
        """
        Bind NumPy data as a logical table.
        data: dict[str, np.ndarray] OR 2D np.ndarray (+ names=[...]).
        """
        tbl = _numpy_to_arrow_table(data, names=names, types=types)
        self.bind_arrow(logical, tbl)

    def bind_records(
        self,
        logical: str,
        rows: list[dict],
        *,
        types: dict | None = None,
    ) -> None:
        """
        Bind list-of-dicts as a logical table (convenience).
        """
        tbl = _records_to_arrow_table(rows, types=types)
        self.bind_arrow(logical, tbl)
    

    # -------- TRANSACTIONS --------
    def begin_tx(self) -> "VelrTx":
        out_tx = ffi.new("velr_tx **")
        out_err = ffi.new("char **")
        rc = lib.velr_tx_begin(self._db, out_tx, out_err)
        _check(rc, out_err)
        return VelrTx(out_tx[0])

# ================= Streaming (outside tx) =================

class Stream:
    __slots__ = ("_st",)
    def __init__(self, st_cdata):
        self._st = st_cdata
    def __del__(self):
        try: self.close()
        except Exception: pass
    def next_table(self) -> Optional["Table"]:
        out_tbl = ffi.new("velr_table **")
        out_has = ffi.new("int *")
        out_err = ffi.new("char **")
        rc = lib.velr_stream_next_table(self._st, out_tbl, out_has, out_err)
        _check(rc, out_err)
        if out_has[0] == 0:
            return None
        return Table(out_tbl[0])
    def iter_tables(self):
        while True:
            t = self.next_table()
            if not t:
                return
            try:
                yield t
            finally:
                t.close()
    def close(self) -> None:
        if self._st != ffi.NULL:
            lib.velr_exec_close(self._st)
            self._st = ffi.NULL
    def __enter__(self) -> "Stream": return self
    def __exit__(self, exc_type, exc, tb): self.close()

# ================= Streaming (inside tx) =================

class StreamTx:
    __slots__ = ("_st",)
    def __init__(self, st_cdata):
        self._st = st_cdata
    def __del__(self):
        try: self.close()
        except Exception: pass
    def next_table(self) -> Optional["Table"]:
        out_tbl = ffi.new("velr_table **")
        out_has = ffi.new("int *")
        out_err = ffi.new("char **")
        rc = lib.velr_stream_tx_next_table(self._st, out_tbl, out_has, out_err)
        _check(rc, out_err)
        if out_has[0] == 0:
            return None
        return Table(out_tbl[0])
    def iter_tables(self):
        while True:
            t = self.next_table()
            if not t:
                return
            try:
                yield t
            finally:
                t.close()
    def close(self) -> None:
        if self._st != ffi.NULL:
            lib.velr_exec_tx_close(self._st)
            self._st = ffi.NULL
    def __enter__(self) -> "StreamTx": return self
    def __exit__(self, exc_type, exc, tb): self.close()

# ================= Table / Rows =================

class Table:
    __slots__ = ("_tbl",)

    # ---- Arrow IPC zero-copy helpers ----
    def _to_ipc_foreign(self) -> _ForeignIPC:
        """
        Get Arrow IPC (file) bytes from Rust in a single foreign allocation.
        Python owns the lifetime and frees via velr_free when no longer referenced.
        """
        out_ptr = ffi.new("unsigned char **")  # must match cdef
        out_len = ffi.new("size_t *")
        out_err = ffi.new("char **")
        rc = lib.velr_table_ipc_file_malloc(self._tbl, out_ptr, out_len, out_err)
        _check(rc, out_err)

        ptr = out_ptr[0]
        ln = int(out_len[0])
        return _ForeignIPC(ptr, ln)

    def to_pyarrow_zero_copy(self):
        """Return a pyarrow.Buffer over the IPC bytes (zero-copy, Python frees)."""
        return self._to_ipc_foreign().to_buffer()

    def to_pyarrow(self):
        return self._to_ipc_foreign().to_pyarrow()

    def to_pandas(self, **kwargs):
        return self._to_ipc_foreign().to_pandas(**kwargs)

    def to_polars(self):
        return self._to_ipc_foreign().to_polars()

    def to_ipc_memoryview(self) -> memoryview:
        return self._to_ipc_foreign().raw_memoryview()

    def to_ipc_bytes(self) -> bytes:
        return self._to_ipc_foreign().to_bytes()

    def write_ipc_to(self, fileobj) -> int:
        return self._to_ipc_foreign().write_to(fileobj)

    def save_ipc(self, path: str) -> None:
        self._to_ipc_foreign().save(path)

    def __init__(self, tbl_cdata):
        self._tbl = tbl_cdata
    def __del__(self):
        try: self.close()
        except Exception: pass
    def column_names(self) -> List[str]:
        n = lib.velr_table_column_count(self._tbl)
        out_ptr = ffi.new("const unsigned char *[1]")
        out_len = ffi.new("size_t[1]")
        names: List[str] = []
        for i in range(n):
            rc = lib.velr_table_column_name(self._tbl, i, out_ptr, out_len)
            if rc != lib.VELR_OK:
                raise VelrError("velr_table_column_name failed")
            b = ffi.string(out_ptr[0], out_len[0])
            names.append(b.decode("utf-8", errors="replace"))
        return names
    def rows(self) -> "Rows":
        out_rows = ffi.new("velr_rows **")
        out_err = ffi.new("char **")
        rc = lib.velr_table_rows_open(self._tbl, out_rows, out_err)
        _check(rc, out_err)
        return Rows(out_rows[0], len(self.column_names()))
    def close(self) -> None:
        if self._tbl != ffi.NULL:
            lib.velr_table_close(self._tbl)
            self._tbl = ffi.NULL
    def __enter__(self) -> "Table": return self
    def __exit__(self, exc_type, exc, tb): self.close()


class Rows:
    __slots__ = ("_rows", "_ncols", "_buf", "_written")
    def __init__(self, rows_cdata, ncols: int):
        self._rows = rows_cdata
        self._ncols = ncols
        self._buf = ffi.new("velr_cell[]", ncols)
        self._written = ffi.new("size_t *")

    def __del__(self):
        try: self.close()
        except Exception: pass

    # iterator protocol
    def __iter__(self):
        return self

    def __next__(self):
        if self._rows == ffi.NULL:
            raise StopIteration
        out_err = ffi.new("char **")
        rc = lib.velr_rows_next(self._rows, self._buf, self._ncols, self._written, out_err)
        if rc < 0:
            raise VelrError(_take_err(out_err))
        if rc == 0:
            raise StopIteration
        n = int(self._written[0])
        row = []
        for i in range(n):
            c = self._buf[i]
            data = ffi.string(c.ptr, c.len) if c.len > 0 else b""
            row.append(Cell(c.ty, int(c.i64_), float(c.f64_), data))
        return tuple(row)

    def close(self) -> None:
        if self._rows != ffi.NULL:
            lib.velr_rows_close(self._rows)
            self._rows = ffi.NULL

    def __enter__(self) -> "Rows": return self
    def __exit__(self, exc_type, exc, tb): self.close()



# ---- drop-in replacement: Savepoint + VelrTx (robust, RAII-safe) ----
import weakref

class Savepoint:
    __slots__ = ("_sp", "_closed", "_parent", "__weakref__")
    def __init__(self, sp_cdata, parent: "VelrTx"):
        # Strong ref keeps tx alive until this SP is closed
        self._sp = sp_cdata
        self._closed = False
        self._parent = parent

    def release(self) -> None:
        if self._sp != ffi.NULL and not self._closed:
            out_err = ffi.new("char **")
            rc = lib.velr_sp_release(self._sp, out_err)
            _check(rc, out_err)
            self._sp = ffi.NULL
            self._closed = True
            # unregister from tx child set
            try: self._parent._unregister_child(self)
            except Exception: pass

    def rollback(self) -> None:
        if self._sp != ffi.NULL and not self._closed:
            out_err = ffi.new("char **")
            rc = lib.velr_sp_rollback(self._sp, out_err)
            _check(rc, out_err)
            self._sp = ffi.NULL
            self._closed = True
            try: self._parent._unregister_child(self)
            except Exception: pass

    def close(self) -> None:
        # Best-effort: if still open, let Rust Drop do safe rollback-to+release.
        if self._sp != ffi.NULL and not self._closed:
            lib.velr_sp_close(self._sp)
            self._sp = ffi.NULL
            self._closed = True
            try: self._parent._unregister_child(self)
            except Exception: pass

    def __del__(self):
        # Avoid raising from GC
        try: self.close()
        except Exception: pass

    def __enter__(self) -> "Savepoint":
        return self

    def __exit__(self, exc_type, exc, tb):
        # Context-manager semantics:
        # - exception -> rollback
        # - clean exit -> release
        if exc_type is not None:
            self.rollback()
        else:
            self.release()


class VelrTx:
    __slots__ = ("_tx", "_closed", "_children")
    def __init__(self, tx_cdata):
        self._tx = tx_cdata
        self._closed = False
        self._children = weakref.WeakSet()


    # ----- tx API -----

    def run(self, cypher: str) -> None:
        with self.exec(cypher) as st:
            while True:
                t = st.next_table()
                if t is None:
                    break
                t.close()
    execute = run


    def exec(self, cypher: str) -> "StreamTx":
        out_st = ffi.new("velr_stream_tx **")
        out_err = ffi.new("char **")
        rc = lib.velr_tx_exec_start(self._tx, cypher.encode(), out_st, out_err)
        _check(rc, out_err)
        return StreamTx(out_st[0])

    def exec_one(self, cypher: str) -> "Table":
        with self.exec(cypher) as st:
            t = st.next_table()
            if t is None:
                raise VelrError("query produced no result tables")
            t2 = st.next_table()
            if t2 is not None:
                t2.close()
                t.close()
                raise VelrError("query produced multiple tables; use exec() to stream them")
            return t

    def savepoint(self) -> Savepoint:
        out_sp = ffi.new("velr_sp **")
        out_err = ffi.new("char **")
        rc = lib.velr_tx_savepoint(self._tx, out_sp, out_err)
        _check(rc, out_err)
        sp = Savepoint(out_sp[0], parent=self)
        self._children.add(sp)
        return sp

    def _unregister_child(self, sp: Savepoint) -> None:
        # Best-effort remove from WeakSet
        try:
            if sp in self._children:
                self._children.discard(sp)
        except Exception:
            pass

    def _close_children_first(self) -> None:
        # Drain all known savepoints *before* touching the tx
        # Copy to list to avoid mutation during iteration.
        for sp in list(self._children):
            try: sp.close()
            except Exception: pass
        self._children.clear()

    def commit(self) -> None:
        if self._tx != ffi.NULL and not self._closed:
            self._close_children_first()
            out_err = ffi.new("char **")
            rc = lib.velr_tx_commit(self._tx, out_err)
            _check(rc, out_err)
            self._tx = ffi.NULL
            self._closed = True

    def rollback(self) -> None:
        if self._tx != ffi.NULL and not self._closed:
            self._close_children_first()
            out_err = ffi.new("char **")
            rc = lib.velr_tx_rollback(self._tx, out_err)
            _check(rc, out_err)
            self._tx = ffi.NULL
            self._closed = True

    def close(self) -> None:
        # IMPORTANT: do NOT call velr_tx_rollback here.
        # close() should only drop the handle; Rust Drop will auto-rollback if still active.
        self._close_children_first()
        if self._tx != ffi.NULL and not self._closed:
            try:
                lib.velr_tx_close(self._tx)  # consumes the handle
            finally:
                self._tx = ffi.NULL
                self._closed = True


    def bind_arrow(self, logical: str, columns) -> None:
        pairs = _normalize_arrow_columns(columns)
        (cols_c, name_views,
        _name_backing, _keep_schemas_nested, _keep_arrays_nested,
        _schema_pp_per_col, _array_pp_per_col) = _export_arrow_columns_for_bind_chunked(pairs)

        out_err = ffi.new("char **")
        logical_c = ffi.new("char[]", logical.encode("utf-8"))
        rc = lib.velr_tx_bind_arrow_chunks(
            self._tx,
            logical_c,
            cols_c,
            name_views,
            len(pairs),
            out_err,
        )
        _check(rc, out_err)

    def bind_pandas(
        self,
        logical: str,
        df: "pd.DataFrame",
        *,
        index: bool = False,
        jsonify_objects: bool = True,
        schema: "Optional['pa.Schema']" = None,
    ) -> None:
        """
        TX-scoped bind for pandas DataFrame; same defaults as Velr.bind_pandas.
        """
        tbl = _pandas_to_arrow_table(df, index=index, jsonify_objects=jsonify_objects, schema=schema)
        self.bind_arrow(logical, tbl)

    def bind_polars(
        self,
        logical: str,
        df: "pl.DataFrame",
        *,
        rechunk: bool = False,
    ) -> None:
        """
        TX-scoped bind for polars DataFrame; same defaults as Velr.bind_polars.
        """
        tbl = _polars_to_arrow_table(df, rechunk=rechunk)
        self.bind_arrow(logical, tbl)


    def bind_numpy(
        self,
        logical: str,
        data,
        *,
        names: list[str] | None = None,
        types: dict | None = None,
    ) -> None:
        tbl = _numpy_to_arrow_table(data, names=names, types=types)
        self.bind_arrow(logical, tbl)

    def bind_records(
        self,
        logical: str,
        rows: list[dict],
        *,
        types: dict | None = None,
    ) -> None:
        tbl = _records_to_arrow_table(rows, types=types)
        self.bind_arrow(logical, tbl)

    
    def __del__(self):
        try:
            if getattr(sys, "is_finalizing", lambda: False)():
                return
            self.close()
        except Exception:
            pass

    def __enter__(self) -> "VelrTx":
        return self

    def __exit__(self, exc_type, exc, tb):
        # RAII parity with Rust: if user didn’t commit, roll back.
        try:
            if self._tx != ffi.NULL and not self._closed:
                self.rollback()
        finally:
            self.close()