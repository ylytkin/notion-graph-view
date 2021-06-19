import networkx as nx
from pyvis.network import Network
from matplotlib.colors import TABLEAU_COLORS

__all__ = [
    'tableau_colors',
    'networkx_graph_to_pyvis_network',
]

tableau_colors = list(TABLEAU_COLORS.values())


def networkx_graph_to_pyvis_network(
        g: nx.Graph,
        node_label: str = 'label',
        node_title: str = 'title',
        node_size: str = 'size',
        node_color: str = 'color',
        edge_weight: str = 'weight',
        height: str = '100%',
        width: str = '100%',
        notebook: bool = False,
        heading: str = '',
        gravity: int = -10000,
) -> Network:
    node_labels = nx.get_node_attributes(g, node_label)
    node_titles = nx.get_node_attributes(g, node_title)
    node_sizes = nx.get_node_attributes(g, node_size)
    node_colors = nx.get_node_attributes(g, node_color)
    edge_widths = nx.get_edge_attributes(g, edge_weight)

    network = Network(height=height, width=width, directed=nx.is_directed(g), notebook=notebook, heading=heading)

    for node in g.nodes:
        label = node_labels.get(node, node)
        title = node_titles.get(node, node)
        size = node_sizes.get(node, 10)
        color = node_colors.get(node, tableau_colors[0])

        network.add_node(node, label=label, title=title, size=float(size), color=color)

    for edge in g.edges:
        width = edge_widths.get(edge, 1)
        network.add_edge(*edge, width=float(width))

    network.barnes_hut(gravity=gravity)

    return network
