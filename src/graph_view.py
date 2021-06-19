from collections import defaultdict

import networkx as nx
import pandas as pd

from config import graph_fpath
from src.db import session
from src.models import Database, Page, Mention
from src.utils import tableau_colors, networkx_graph_to_pyvis_network

__all__ = [
    'build_graph',
    'display_graph',
]


def build_graph() -> nx.DiGraph:
    databases = session.query(Database).all()

    database_titles = {database.id: database.title for database in databases}
    database_colors = {
        database.id: tableau_colors[i % len(tableau_colors)]
        for i, database in enumerate(databases)
    }

    pages = session.query(Page).all()
    page_labels = {page.id: page.title for page in pages}
    page_colors = {page.id: database_colors.get(page.database_id, '#000000') for page in pages}

    page_titles = {}

    for page in pages:
        title = f'{page.title}<br/><br/>Database: {database_titles.get(page.database_id)}'

        if page.url:
            title += f'<br/>URL: {page.url}'

        page_titles[page.id] = title

    nodes = set(page_labels)

    edge_weights = defaultdict(int)

    for mention in session.query(Mention).all():
        i = mention.page_id
        j = mention.mentioned_id

        edge_weights[(i, j)] += 1

    edges = [(i, j, w) for (i, j), w in edge_weights.items()]

    g = nx.DiGraph()
    g.add_weighted_edges_from(edges)
    g = g.subgraph(nodes).copy()

    nx.set_node_attributes(g, page_labels, name='label')
    nx.set_node_attributes(g, page_titles, name='title')
    nx.set_node_attributes(g, page_colors, name='color')

    node_size = pd.Series(dict(nx.degree(g.to_undirected()))) + 5
    nx.set_node_attributes(g, node_size, name='size')

    return g


def display_graph(g: nx.DiGraph):
    network = networkx_graph_to_pyvis_network(g, height='100%', notebook=False, gravity=-50000)

    network.show(graph_fpath.as_posix())
