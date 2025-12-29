# velrpy/src/velrpy/_ffi.py
from __future__ import annotations
import os
import sys
import ctypes
from pathlib import Path
from contextlib import contextmanager, suppress
import importlib.resources as ir
from cffi import FFI

ffi = FFI()

# ---------------- C declarations (drop-in replacement) ----------------
ffi.cdef(r"""
typedef struct velr_db          velr_db;
typedef struct velr_stream      velr_stream;
typedef struct velr_table       velr_table;
typedef struct velr_rows        velr_rows;
typedef struct velr_tx          velr_tx;
typedef struct velr_sp          velr_sp;
typedef struct velr_stream_tx   velr_stream_tx;

typedef enum velr_code {
  VELR_OK     = 0,
  VELR_EARG   = -1,
  VELR_EUTF   = -2,
  VELR_ESTATE = -3,
  VELR_EERR   = -4,
} velr_code;

typedef enum velr_cell_type {
  VELR_NULL   = 0,
  VELR_BOOL   = 1,
  VELR_INT64  = 2,
  VELR_DOUBLE = 3,
  VELR_TEXT   = 4,
  VELR_JSON   = 5,
} velr_cell_type;

typedef struct velr_cell {
  velr_cell_type        ty;
  long long             i64_;
  double                f64_;
  const unsigned char*  ptr;
  size_t                len;
} velr_cell;

void velr_string_free(char* s);

/* DB */
velr_code velr_open (const char* path_or_null, velr_db** out_db, char** out_err);
void      velr_close(velr_db* db);

/* Exec outside tx */
velr_code velr_exec_start(velr_db* db, const char* cypher, velr_stream** out_stream, char** out_err);
velr_code velr_exec_one  (velr_db* db, const char* cypher, velr_table** out_table, char** out_err);
velr_code velr_stream_next_table(velr_stream* stream, velr_table** out_table, int* out_has, char** out_err);
void      velr_exec_close(velr_stream* stream);

/* Table / Rows */
size_t    velr_table_column_count(velr_table* table);
velr_code velr_table_column_name(velr_table* table, size_t idx,
                                 const unsigned char** out_ptr, size_t* out_len);
velr_code velr_table_rows_open(velr_table* table, velr_rows** out_rows, char** out_err);
void      velr_table_close(velr_table* table);

int       velr_rows_next(velr_rows* rows, struct velr_cell* buf, size_t buf_len,
                         size_t* out_written, char** out_err);
void      velr_rows_close(velr_rows* rows);

/* Transactions */
velr_code velr_tx_begin   (velr_db* db, velr_tx** out_tx, char** out_err);
velr_code velr_tx_commit  (velr_tx* tx, char** out_err);
velr_code velr_tx_rollback(velr_tx* tx, char** out_err);
void      velr_tx_close   (velr_tx* tx);

velr_code velr_tx_exec_start(velr_tx* tx, const char* cypher,
                             velr_stream_tx** out_stream, char** out_err);
velr_code velr_stream_tx_next_table(velr_stream_tx* stream, velr_table** out_table,
                                    int* out_has, char** out_err);
void      velr_exec_tx_close(velr_stream_tx* stream);

/* Savepoints */
velr_code velr_tx_savepoint(velr_tx* tx, velr_sp** out_sp, char** out_err);
velr_code velr_sp_release  (velr_sp* sp, char** out_err);
velr_code velr_sp_rollback (velr_sp* sp, char** out_err);
void      velr_sp_close    (velr_sp* sp);

/* Optional named savepoint helpers (present in your Rust FFI) */
velr_code velr_tx_savepoint_named(velr_tx* tx, const char* name, velr_sp** out_sp, char** out_err);
velr_code velr_tx_rollback_to    (velr_tx* tx, const char* name, char** out_err);

/* ========== Arrow IPC (file) helpers ========== */
/* These are compiled behind Rust feature `arrow-ipc`. */
velr_code velr_table_ipc_file_len(
    velr_table* table,
    size_t* out_len,
    char** out_err);

velr_code velr_table_ipc_file_write(
    velr_table* table,
    unsigned char* dst_ptr,
    size_t dst_len,
    size_t* out_written,
    char** out_err);

velr_code velr_table_ipc_file_malloc(
    velr_table* table,
    unsigned char** out_ptr,
    size_t* out_len,
    char** out_err);

/* ----- Arrow C Data forward decls ----- */
struct ArrowSchema;
struct ArrowArray;

/* velr_strview (for column names) */
typedef struct velr_strview {
  const unsigned char* ptr;  /* not NUL-terminated */
  size_t               len;
} velr_strview;

/* ----- Non-chunked zero-copy Arrow column binding ----- */
velr_code velr_bind_arrow(
    velr_db* db,
    const char* logical,
    const struct ArrowSchema* const* schemas,
    const struct ArrowArray*  const* arrays,
    const velr_strview* colnames,
    size_t col_count,
    char** out_err);

velr_code velr_tx_bind_arrow(
    velr_tx* tx,
    const char* logical,
    const struct ArrowSchema* const* schemas,
    const struct ArrowArray*  const* arrays,
    const velr_strview* colnames,
    size_t col_count,
    char** out_err);

/* ----- NEW: per-column chunked Arrow binding ----- */
typedef struct velr_arrow_chunks {
  const struct ArrowSchema* const* schemas;  /* len = chunk_count */
  const struct ArrowArray*  const* arrays;   /* len = chunk_count */
  size_t chunk_count;
} velr_arrow_chunks;

velr_code velr_bind_arrow_chunks(
    velr_db* db,
    const char* logical,
    const struct velr_arrow_chunks* cols,     /* len = col_count */
    const struct velr_strview*      colnames, /* len = col_count */
    size_t col_count,
    char** out_err);

velr_code velr_tx_bind_arrow_chunks(
    velr_tx* tx,
    const char* logical,
    const struct velr_arrow_chunks* cols,     /* len = col_count */
    const struct velr_strview*      colnames, /* len = col_count */
    size_t col_count,
    char** out_err);

/* Rust-side deallocator for buffers returned by velr_table_ipc_file_malloc */
void velr_free(unsigned char* p, size_t len);
""")


# ---------------- Platform helpers ----------------

def _platform_names() -> list[str]:
    if sys.platform.startswith("darwin"):
        return ["libvelrc.dylib", "velrc.dylib"]
    if sys.platform.startswith("win"):
        return ["velrc.dll"]
    # linux & everything else assumed ELF
    return ["libvelrc.so", "velrc.so"]

def _iter_candidate_paths() -> list[Path]:
    """
    Strict: only search the vendored location inside the wheel/editable install:
        <package>/velrpy/_vendor/<platform-lib-name>
    No environment overrides (e.g., VELR_LIB), no PATH/LD/DYLD, no cwd fallbacks.
    """
    here = Path(__file__).resolve()
    vendor_dir = here.parent / "_vendor"
    names = _platform_names()

    out: list[Path] = []
    for n in names:
        p = (vendor_dir / n)
        if p.exists():
            out.append(p.resolve())
    return out

@contextmanager
def _windows_dll_dir(path: Path):
    if not sys.platform.startswith("win"):
        yield
        return
    add_dir = getattr(os, "add_dll_directory", None)
    if add_dir is None:
        yield
        return
    handle = None
    try:
        handle = add_dir(str(path))
        yield
    finally:
        if handle is not None:
            with suppress(Exception):
                handle.close()


def _try_dlopen(candidates: list[Path]) -> object:
    last_err: Exception | None = None

    # Only try the vendored copies we found.
    for p in candidates:
        try:
            if sys.platform.startswith("win"):
                with _windows_dll_dir(p.parent):
                    return ffi.dlopen(str(p))
            return ffi.dlopen(str(p))
        except OSError as e:
            last_err = e

    # Nothing worked — hard fail with a precise message.
    vendor_msg = str((Path(__file__).resolve().parent / "_vendor").resolve())
    cand_lines = ["  - " + str(p) for p in candidates]
    if not cand_lines:
        cand_lines = ["  - <no files present>"]

    msg_lines = [
        "velrpy: failed to locate/load the native library from the vendored wheel location.",
        f"Platform: {sys.platform}",
        "Checked:",
        *cand_lines,
        "",
        "Expected the library to be bundled under:",
        f"  {vendor_msg}",
        "",
        "Fixes:",
        "  * Reinstall velrpy from a wheel (pip install velrpy).",
        "  * Ensure _vendor/ contains the platform library.",
        "  * Make sure Python arch matches the wheel (e.g. arm64 vs x86_64).",
    ]
    if last_err:
        msg_lines += ["", "Last dlopen error: " + str(last_err)]
    raise OSError("\n".join(msg_lines))

def _dlopen():
    candidates = _iter_candidate_paths()
    return _try_dlopen(candidates)

# The loaded C-ABI library handle
lib = _dlopen()

