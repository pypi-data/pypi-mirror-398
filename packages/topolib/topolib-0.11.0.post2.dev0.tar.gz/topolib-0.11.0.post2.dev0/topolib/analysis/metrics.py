"""
Metrics module for network topology analysis.
"""

import warnings
from typing import List, Dict, Optional

import networkx as nx
import numpy as np
from numpy.typing import NDArray
import scipy.sparse as sp  # type: ignore[import-untyped]

from topolib.topology import Topology


class Metrics:
    """
    Provides static methods for computing metrics on network topologies.

    All methods receive a Topology instance.

    Methods
    -------
    node_degree(topology)
        Calculates the degree of each node.
    average_node_degree(topology)
        Calculates the average node degree.
    diameter(topology)
        Calculates the network diameter.
    network_density(topology)
        Calculates the network density.
    average_shortest_path_length(topology)
        Calculates the average shortest path length.
    clustering_coefficient(topology)
        Calculates the average clustering coefficient.
    max_edge_betweenness(topology)
        Calculates the maximum edge betweenness centrality.
    max_node_betweenness(topology)
        Calculates the maximum node betweenness centrality.
    global_efficiency(topology)
        Calculates the global efficiency.
    spectral_radius(topology)
        Calculates the spectral radius.
    algebraic_connectivity(topology)
        Calculates the algebraic connectivity.
    weighted_spectral_distribution(topology)
        Calculates the weighted spectral distribution.
    average_link_length(topology)
        Calculates the average physical link length.
    betweenness_centrality(topology)
        Calculates betweenness centrality for each node.
    closeness_centrality(topology)
        Calculates closeness centrality for each node.
    eigenvector_centrality(topology)
        Calculates eigenvector centrality for each node.
    edge_betweenness_centrality(topology)
        Calculates edge betweenness centrality for each link.
    link_length_stats(topology)
        Calculates statistics (min, max, avg) of link lengths.
    connection_matrix(topology)
        Builds the adjacency matrix.
    """

    @staticmethod
    def node_degree(topology: "Topology") -> Dict[int, int]:
        """
        Calculates the degree of each node in the topology.

        For bidirectional links (where both A->B and B->A exist),
        each node's degree is incremented only once per connection.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: degree}
        :rtype: dict[int, int]
        """
        degree = {n.id: 0 for n in topology.nodes}
        # Use a set to track processed link pairs to avoid double counting
        processed_pairs: set[tuple[int, int]] = set()

        for link in topology.links:
            # Create a normalized pair (smaller_id, larger_id) to detect bidirectional links
            pair: tuple[int, int] = (
                min(link.source.id, link.target.id),
                max(link.source.id, link.target.id),
            )

            if pair not in processed_pairs:
                processed_pairs.add(pair)
                degree[link.source.id] += 1
                degree[link.target.id] += 1

        return degree

    @staticmethod
    def link_length_stats(topology: "Topology") -> Dict[str, Optional[float]]:
        """
        Calculates the minimum, maximum, and average link lengths.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary with keys 'min', 'max', 'avg'.
        :rtype: dict[str, float | None]
        """
        lengths = [l.length for l in topology.links]
        if not lengths:
            return {"min": None, "max": None, "avg": None}
        return {
            "min": min(lengths),
            "max": max(lengths),
            "avg": sum(lengths) / len(lengths),
        }

    @staticmethod
    def connection_matrix(topology: "Topology") -> List[List[int]]:
        """
        Builds the adjacency matrix of the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Adjacency matrix (1 if connected, 0 otherwise).
        :rtype: list[list[int]]
        """
        id_to_idx = {n.id: i for i, n in enumerate(topology.nodes)}
        size = len(topology.nodes)
        matrix = [[0] * size for _ in range(size)]
        for link in topology.links:
            i = id_to_idx[link.source.id]
            j = id_to_idx[link.target.id]
            matrix[i][j] = 1
            matrix[j][i] = 1
        return matrix

    @staticmethod
    def average_node_degree(topology: "Topology") -> float:
        """
        Calculates the average node degree of the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average node degree
        :rtype: float
        """
        degrees = Metrics.node_degree(topology)
        if not degrees:
            return 0.0
        return sum(degrees.values()) / len(degrees)

    @staticmethod
    def diameter(topology: "Topology") -> Optional[int]:
        """
        Calculates the network diameter (longest shortest path).

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Network diameter, or None if network is disconnected
        :rtype: int | None
        """
        G = topology.graph.to_undirected()
        if not nx.is_connected(G):
            return None
        return nx.diameter(G)

    @staticmethod
    def average_shortest_path_length(topology: "Topology") -> Optional[float]:
        """
        Calculates the average shortest path length between all pairs of nodes.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average shortest path length, or None if network is disconnected
        :rtype: float | None
        """
        G = topology.graph.to_undirected()
        if not nx.is_connected(G):
            return None
        return nx.average_shortest_path_length(G)

    @staticmethod
    def clustering_coefficient(topology: "Topology") -> float:
        """
        Calculates the average clustering coefficient of the network.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average clustering coefficient
        :rtype: float
        """
        G = topology.graph.to_undirected()
        return nx.average_clustering(G)

    @staticmethod
    def algebraic_connectivity(topology: "Topology") -> float:
        """
        Calculates the algebraic connectivity (second smallest eigenvalue of the Laplacian matrix).

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Algebraic connectivity
        :rtype: float
        """
        G = topology.graph.to_undirected()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            return nx.algebraic_connectivity(G)

    @staticmethod
    def average_link_length(topology: "Topology") -> Optional[float]:
        """
        Calculates the average physical link length in the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Average link length
        :rtype: float | None
        """
        return Metrics.link_length_stats(topology)["avg"]

    @staticmethod
    def betweenness_centrality(topology: "Topology") -> Dict[int, float]:
        """
        Calculates the betweenness centrality for each node.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: betweenness_centrality}
        :rtype: dict[int, float]
        """
        G = topology.graph.to_undirected()
        return nx.betweenness_centrality(G)

    @staticmethod
    def closeness_centrality(topology: "Topology") -> Dict[int, float]:
        """
        Calculates the closeness centrality for each node.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: closeness_centrality}
        :rtype: dict[int, float]
        """
        G = topology.graph.to_undirected()
        return nx.closeness_centrality(G)  # type: ignore[no-any-return]

    @staticmethod
    def eigenvector_centrality(topology: "Topology") -> Dict[int, float]:
        """
        Calculates the eigenvector centrality for each node.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: eigenvector_centrality}
        :rtype: dict[int, float]
        """
        G = topology.graph.to_undirected()
        try:
            return nx.eigenvector_centrality(G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            return nx.eigenvector_centrality(G, max_iter=10000)

    @staticmethod
    def edge_betweenness_centrality(
        topology: "Topology",
    ) -> Dict[tuple[int, int], float]:
        """
        Calculates the edge betweenness centrality for each link.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {(source_id, target_id): edge_betweenness}
        :rtype: dict[tuple[int, int], float]
        """
        G = topology.graph.to_undirected()
        return nx.edge_betweenness_centrality(G)

    @staticmethod
    def network_density(topology: "Topology") -> float:
        """
        Calculates the network density (ratio of actual edges to maximum possible edges).
        Formula: ND = 2m / (n(n-1)) where m is number of edges and n is number of nodes.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Network density
        :rtype: float
        """
        G = topology.graph.to_undirected()
        return float(nx.density(G))  # type: ignore[arg-type]

    @staticmethod
    def max_edge_betweenness(topology: "Topology") -> float:
        """
        Calculates the maximum edge betweenness centrality in the network.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Maximum edge betweenness centrality
        :rtype: float
        """
        edge_bc = Metrics.edge_betweenness_centrality(topology)
        if not edge_bc:
            return 0.0
        return max(edge_bc.values())

    @staticmethod
    def max_node_betweenness(topology: "Topology") -> float:
        """
        Calculates the maximum node betweenness centrality in the network.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Maximum node betweenness centrality
        :rtype: float
        """
        node_bc = Metrics.betweenness_centrality(topology)
        if not node_bc:
            return 0.0
        return max(node_bc.values())

    @staticmethod
    def global_efficiency(topology: "Topology") -> float:
        """
        Calculates the global efficiency of the network.
        Formula: E_glob = 1/(n(n-1)) * sum(1/d(u,v)) for all u != v

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Global efficiency
        :rtype: float
        """
        G = topology.graph.to_undirected()
        return nx.global_efficiency(G)

    @staticmethod
    def spectral_radius(topology: "Topology") -> float:
        """
        Calculates the spectral radius (largest absolute eigenvalue of adjacency matrix).

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Spectral radius
        :rtype: float
        """
        G = topology.graph.to_undirected()
        # Use to_scipy_sparse_array to avoid deprecation warnings
        adj_sparse = nx.to_scipy_sparse_array(G)  # type: ignore[no-untyped-call]
        # Convert to dense numpy array for eigenvalue calculation
        adj_array: NDArray[np.float64] = adj_sparse.toarray()  # type: ignore[attr-defined]
        eigenvalues = np.linalg.eigvals(adj_array)  # type: ignore[arg-type]
        return float(np.max(np.abs(eigenvalues)))

    @staticmethod
    def weighted_spectral_distribution(topology: "Topology") -> float:
        """
        Calculates the weighted spectral distribution of the normalized Laplacian.
        Formula: WSD(G) = sum((1-k) * N_f(lambda_L^D = k)) for k in K

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Weighted spectral distribution
        :rtype: float
        """
        G = topology.graph.to_undirected()
        # Compute normalized Laplacian eigenvalues
        # Use scipy.sparse.csgraph to avoid NetworkX deprecation warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            laplacian_sparse = nx.normalized_laplacian_matrix(G)
        # Convert to dense numpy array for eigenvalue calculation
        laplacian_array: NDArray[np.float64]
        if sp.issparse(laplacian_sparse):  # type: ignore[no-untyped-call]
            laplacian_array = laplacian_sparse.toarray()  # type: ignore[attr-defined]
        else:
            laplacian_array = np.array(laplacian_sparse)
        eigenvalues = np.linalg.eigvalsh(laplacian_array)  # type: ignore[arg-type]

        # Bin eigenvalues and compute weighted sum
        hist, bin_edges = np.histogram(eigenvalues, bins=50)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        wsd = np.sum((1 - bin_centers) * hist)

        return float(wsd)
