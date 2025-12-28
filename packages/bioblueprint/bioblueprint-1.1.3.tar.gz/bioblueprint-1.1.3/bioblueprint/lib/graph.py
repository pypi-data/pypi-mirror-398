#! /usr/bin/env python3

import logging
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


def get_root_nodes(G):
    """Get root nodes of the graph"""
    return [n for n, d in G.in_degree() if d == 0]


def get_leaf_nodes(G):
    """Get leaf nodes of the graph"""
    return [n for n, d in G.out_degree() if d == 0]


def obtain_graph_paths(G, nodes, root_nodes=None):
    """Obtain the paths from the root workflows through a node in the graph"""
    if not root_nodes:
        root_nodes = get_root_nodes(G)
    perturbed_roots = defaultdict(list)
    for node in nodes:
        for root in root_nodes:
            root_paths = list(nx.all_simple_paths(G, source=root, target=node))
            if root_paths:
                perturbed_roots[root].append(node)
                logger.info(f"{root[1]} affected by {node[1]}")
                continue
    return perturbed_roots
