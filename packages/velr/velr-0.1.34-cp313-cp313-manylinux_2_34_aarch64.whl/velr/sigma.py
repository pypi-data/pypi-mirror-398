# velr/sigma.py
from __future__ import annotations
import networkx as nx
from ipysigma import Sigma


def explore(
    G: nx.Graph,
    *,
    height: int = 500,
    theme: str = "light",
    **kwargs,
) -> Sigma:
    """
    Explore a graph using ipysigma with a Neo4j Bloom-like visual & layout preset.

    Assumes nodes may have:
        - category: primary label used for coloring
        - importance: numeric score used for node size (e.g. degree)
        - caption: human-readable label (name/title)
    and edges may have:
        - rel: relationship type
    """

    # --- Theme presets ----------------------------------------------------
    if theme == "dark":
        # Roughly aligned with VS Code Dark+
        theme_defaults = dict(
            background_color="#1e1e1e",
            default_node_color="#9ca3af",      # neutral-ish grey
            default_edge_color="#4b5563",      # darker grey
            default_node_label_color="#d4d4d4",
            label_font="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        )
    elif theme == "light":
        theme_defaults = dict(
            background_color="white",
            default_node_color="#999999",
            default_edge_color="#bbbbbb",
            default_node_label_color="black",
            label_font="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        )
    else:
        raise ValueError(f"Unknown theme '{theme}', expected 'light' or 'dark'.")

    # --- Bloom-like ForceAtlas2 layout -----------------------------------
    layout_defaults = dict(
        layout_settings={
            "slowDown": 5,
            "gravity": 2.0,
            "strongGravityMode": True,
            "scalingRatio": 2.0,
            "edgeWeightInfluence": 0.5,
            "outboundAttractionDistribution": False,
            "adjustSizes": True,
        }
    )

    # --- Core visual preset ----------------------------------------------
    core_defaults = dict(
        # Run FA2 ~5 seconds, then freeze in a nice stable layout
        start_layout=5,
        height=height,

        # Nodes
        node_color="category",
        node_size="importance",
        node_size_scale="log+1",
        node_size_range=(4, 20),
        node_label="caption",
        # Slightly smaller labels so edge text feels less shouty
        node_label_size_range=(8, 18),
        default_node_label_size=11,
        node_border_color_from="node",

        # Edges
        edge_color="rel",
        default_edge_type="curve",
        edge_size_range=(0.5, 3),
        edge_label="rel",
    )

    # Merge: core -> layout -> theme -> user kwargs (user wins)
    defaults: dict = {}
    defaults.update(core_defaults)
    defaults.update(layout_defaults)
    defaults.update(theme_defaults)
    defaults.update(kwargs)

    return Sigma(G, **defaults)


