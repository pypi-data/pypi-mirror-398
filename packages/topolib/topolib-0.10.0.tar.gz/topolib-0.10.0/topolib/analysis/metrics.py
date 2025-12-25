"""
Metrics module for network topology analysis.
"""

from typing import List, Dict, Optional


from topolib.topology import Topology


class Metrics:
    """
    Provides static methods for computing metrics on network topologies.

    All methods receive a Topology instance.

    Methods
    -------
    node_degree(topology)
        Calculates the degree of each node.
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
