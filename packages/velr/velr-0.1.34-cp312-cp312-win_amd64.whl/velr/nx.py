import networkx as nx
from typing import Any, Optional, Sequence, Hashable

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

try:
    import polars as pl
except ImportError:  # pragma: no cover
    pl = None


def from_frame(
    frame: Any,
    *,
    src: Optional[str] = None,
    dst: Optional[str] = None,
    rel_col: Optional[str] = None,
    directed: bool = True,
    multigraph: bool = False,
    rel_as_key: bool = False,
    # New Bloom-style options (all optional, backwards compatible)
    src_labels_col: Optional[str] = None,
    dst_labels_col: Optional[str] = None,
    src_title_cols: Optional[Sequence[str]] = None,
    dst_title_cols: Optional[Sequence[str]] = None,
) -> nx.Graph:
    """
    Build a NetworkX graph from a pandas or Polars DataFrame.

    Each row in the frame is interpreted as an edge.

    Conventions
    -----------
    - Two columns define the edge endpoints:
        * src: source node
        * dst: target node
    - An optional column defines the relationship type:
        * rel_col: e.g. 'rel' or 'rel_type'
    - All remaining columns are stored as edge attributes.
    - Optionally, you can enrich nodes with Bloom-style metadata:
        * src_labels_col / dst_labels_col: list[str] of labels per endpoint.
        * src_title_cols / dst_title_cols: columns to derive a readable title.

    Parameters
    ----------
    frame :
        pandas.DataFrame or polars.DataFrame where each row is an edge.
    src :
        Name of the source-node column.
        If None, uses 'src' if present, otherwise frame.columns[0].
    dst :
        Name of the destination-node column.
        If None, uses 'dst' if present, otherwise frame.columns[1].
    rel_col :
        Optional relation-type column name. If given, its value is stored
        as an edge attribute under that name. If `multigraph` and
        `rel_as_key` are True, the relation type is also used as the
        edge key.
    directed :
        If True, return a DiGraph / MultiDiGraph. Otherwise Graph / MultiGraph.
    multigraph :
        If True, build a Multi(Graph/DiGraph) so parallel edges are allowed.
    rel_as_key :
        If True and both `multigraph` and `rel_col` are set, use the relation
        type value as the edge key. Otherwise keys are auto-assigned.
    src_labels_col / dst_labels_col :
        Optional column names containing a list[str] of labels for the
        source / destination node (e.g. result of labels(a), labels(b)).
        These are aggregated into a node attribute "labels".
        The columns remain available as edge attributes as well.
    src_title_cols / dst_title_cols :
        Optional sequences of column names from which to derive a human
        readable node title:
            - If None, defaults to (src,) and (dst,) respectively.
        The chosen titles are aggregated into node attribute "titles" and
        summarized into "bloom_title".

    Returns
    -------
    G :
        A NetworkX Graph/DiGraph/MultiGraph/MultiDiGraph with additional
        node attributes:
            - labels: list[str]
            - bloom_label: str
            - bloom_title: str
            - bloom_size: int (degree)
    """
    if frame is None:
        raise ValueError("frame must not be None")

    cols, get_len, get_value = _frame_accessors(frame)

    if len(cols) < 2:
        raise ValueError("Frame must have at least two columns to build a graph")

    # Determine src/dst
    if src is None:
        src = "src" if "src" in cols else cols[0]
    if dst is None:
        dst = "dst" if "dst" in cols else cols[1]

    if src not in cols or dst not in cols:
        raise ValueError(
            f"Source column '{src}' or destination column '{dst}' "
            f"not found in frame columns {cols}"
        )

    if rel_col is not None and rel_col not in cols:
        raise ValueError(
            f"Relation column '{rel_col}' not found in frame columns {cols}"
        )

    # Default title cols if not provided
    if src_title_cols is None:
        src_title_cols = (src,)
    if dst_title_cols is None:
        dst_title_cols = (dst,)

    # Choose graph type
    if multigraph:
        G: nx.Graph = nx.MultiDiGraph() if directed else nx.MultiGraph()
    else:
        G = nx.DiGraph() if directed else nx.Graph()

    # Everything except src/dst/(rel_col) is an edge attribute
    excluded = {src, dst}
    if rel_col is not None:
        excluded.add(rel_col)
    edge_attr_cols = [c for c in cols if c not in excluded]

    n = get_len()

    def _ensure_list(x):
        if x is None:
            return []
        if isinstance(x, (list, tuple)):
            return list(x)
        # labels(a)/labels(b) should already be a list[str]; fall back gracefully
        return [x]

    def _pick_title(row_idx: int, title_cols: Sequence[str]) -> Optional[str]:
        for c in title_cols:
            if c in cols:
                v = get_value(c, row_idx)
                if v is not None:
                    s = str(v)
                    if s.strip():
                        return s
        return None

    for i in range(n):
        u = get_value(src, i)
        v = get_value(dst, i)

        attrs = {c: get_value(c, i) for c in edge_attr_cols}

        key = None
        if rel_col is not None:
            rel_val = get_value(rel_col, i)
            attrs[rel_col] = rel_val
            if multigraph and rel_as_key:
                key = rel_val

        if multigraph and key is not None:
            G.add_edge(u, v, key=key, **attrs)
        else:
            G.add_edge(u, v, **attrs)

        # --- Bloom-style node enrichment (optional) ---

        # labels(a)/labels(b) as node labels
        if src_labels_col and src_labels_col in cols:
            u_labels = _ensure_list(get_value(src_labels_col, i))
            _update_node_labels(G, u, u_labels)

        if dst_labels_col and dst_labels_col in cols:
            v_labels = _ensure_list(get_value(dst_labels_col, i))
            _update_node_labels(G, v, v_labels)

        # Titles (names) from configurable columns
        u_title = _pick_title(i, src_title_cols)
        if u_title:
            G.nodes[u].setdefault("titles", set()).add(u_title)

        v_title = _pick_title(i, dst_title_cols)
        if v_title:
            G.nodes[v].setdefault("titles", set()).add(v_title)

    # Finalize node attributes: normalize labels/titles and add visual helpers
    for node, data in G.nodes(data=True):
        labels = data.get("labels")
        if labels is None:
            labels = []
        data["labels"] = list(labels)

        titles = data.get("titles")
        if titles is None:
            titles = []
        else:
            titles = [str(t) for t in titles]
        data["titles"] = list(titles)

        # Primary label → category (for styling/coloring)
        primary_label = data["labels"][0] if data["labels"] else "Node"
        data["category"] = primary_label

        # Primary title → caption (for display text)
        primary_title = data["titles"][0] if data["titles"] else str(node)
        data["caption"] = primary_title

        # Simple importance metric (used for node size)
        data["importance"] = G.degree(node)


    return G


def _frame_accessors(frame: Any):
    """
    Return (columns, get_len, get_value) for pandas or Polars, without
    converting between them.
    """
    # pandas
    if pd is not None and isinstance(frame, pd.DataFrame):
        cols = list(frame.columns)
        # cache columns as numpy arrays, no extra pandas DataFrame copy
        series_cache = {c: frame[c].to_numpy(copy=False) for c in cols}

        def get_len() -> int:
            return len(frame)

        def get_value(col: str, idx: int):
            return series_cache[col][idx]

        return cols, get_len, get_value

    # polars
    if pl is not None and isinstance(frame, pl.DataFrame):
        cols = frame.columns
        # cache columns as Polars Series (no conversion to pandas)
        series_cache = {c: frame[c] for c in cols}

        def get_len() -> int:
            return frame.height

        def get_value(col: str, idx: int):
            # indexing a Polars Series returns a Python scalar
            return series_cache[col][idx]

        return cols, get_len, get_value

    raise TypeError(
        "Unsupported frame type; expected pandas.DataFrame or polars.DataFrame"
    )


def _update_node_labels(G: nx.Graph, node: Hashable, labels: list[str]) -> None:
    """
    Merge a list of labels into the node's "labels" attribute, keeping uniqueness.
    """
    data = G.nodes[node]
    current = data.get("labels")
    if current is None:
        data["labels"] = list(dict.fromkeys(labels))
    else:
        merged = list(dict.fromkeys(list(current) + list(labels)))
        data["labels"] = merged



def _frame_accessors(frame: Any):
    """
    Return (columns, get_len, get_value) for pandas or Polars, without
    converting between them.
    """
    # pandas
    if pd is not None and isinstance(frame, pd.DataFrame):
        cols = list(frame.columns)
        # cache columns as numpy arrays, no extra pandas DataFrame copy
        series_cache = {c: frame[c].to_numpy(copy=False) for c in cols}

        def get_len() -> int:
            return len(frame)

        def get_value(col: str, idx: int):
            return series_cache[col][idx]

        return cols, get_len, get_value

    # polars
    if pl is not None and isinstance(frame, pl.DataFrame):
        cols = frame.columns
        # cache columns as Polars Series (no conversion to pandas)
        series_cache = {c: frame[c] for c in cols}

        def get_len() -> int:
            return frame.height

        def get_value(col: str, idx: int):
            # indexing a Polars Series returns a Python scalar
            return series_cache[col][idx]

        return cols, get_len, get_value

    raise TypeError(
        "Unsupported frame type; expected pandas.DataFrame or polars.DataFrame"
    )
