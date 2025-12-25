"""
Traffic matrix generation module.

This module provides methods to generate traffic demand matrices using different models:
- Gravitational model (population-based)
- DC/IXP model (datacenter and internet exchange point-based)
- Distribution probability model (resource-based traffic distribution)
"""

from typing import Dict, Tuple, List, Any, TYPE_CHECKING
import itertools
import json
import math
import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ..topology.topology import Topology


class TrafficMatrix:
    """
    Traffic matrix generator for network topologies.

    Generates traffic demand matrices between nodes using different models.
    All matrices are returned as numpy arrays where matrix[i][j] represents
    traffic from node i to node j (in Gbps).

    All methods are static and receive a Topology instance as parameter.
    """

    @staticmethod
    def _calculate_node_degrees(topology: "Topology") -> Dict[int, int]:
        """
        Calculate the degree (number of connections) for each node.

        Parameters
        ----------
        topology : Topology
            The network topology.

        Returns
        -------
        dict
            Dictionary mapping node_id to degree count.
        """
        degree_counts = {node.id: 0 for node in topology.nodes}
        processed_links: set[Tuple[int, int]] = set()

        for link in topology.links:
            # Treat links as bidirectional for degree counting
            link_tuple: Tuple[int, int] = tuple(sorted((link.source.id, link.target.id)))  # type: ignore
            if link_tuple not in processed_links:
                degree_counts[link.source.id] += 1
                degree_counts[link.target.id] += 1
                processed_links.add(link_tuple)

        return degree_counts

    @staticmethod
    def _get_gravitational_k(topology: "Topology", rate: float = 0.015) -> float:
        """
        Calculate the K constant for the gravitational model.

        Parameters
        ----------
        topology : Topology
            The network topology.
        rate : float
            Traffic rate per population unit (default: 0.015 Gbps per capita)

        Returns
        -------
        float
            The K constant for the gravitational formula.
        """
        nodes = list(topology.nodes)
        if len(nodes) < 2:
            return 0.0

        total_pop = sum(node.pop for node in nodes)
        sum_pop_pairs = sum(
            n1.pop * n2.pop for n1, n2 in itertools.combinations(nodes, 2)
        )

        if sum_pop_pairs == 0:
            return 0.0

        return (rate * total_pop) / sum_pop_pairs

    @staticmethod
    def _pre_calculate_metrics(
        topology: "Topology",
        w_pop: float = 0.015,
        w_dc: float = 400.0,
        w_ixp: float = 2857.0,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 1.0,
    ) -> Tuple[Dict[int, Dict[str, float]], float]:
        """
        Pre-calculate metrics for distribution probability model.

        Parameters
        ----------
        topology : Topology
            The network topology.
        w_pop : float
            Weight for population (Gbps per capita)
        w_dc : float
            Weight for datacenter capacity (Gbps per DC)
        w_ixp : float
            Weight for IXP capacity (Gbps per IXP)
        alpha : float
            Proportion of population data to use (default: 1.0)
        beta : float
            Proportion of datacenter data to use (default: 1.0)
        gamma : float
            Proportion of IXP data to use (default: 1.0)

        Returns
        -------
        tuple
            (stats_lookup, total_size_N) where stats_lookup contains
            share_pct and traffic_leaving for each node.
        """
        # Calculate traffic and sizes
        temp_data: List[Dict[str, Any]] = []
        total_size_N = 0.0

        for node in topology.nodes:
            # Weighted sum (Traffic n_i) with importance factors
            traffic_ni = (
                (alpha * node.pop * w_pop)
                + (beta * node.dc * w_dc)
                + (gamma * node.ixp * w_ixp)
            )
            # Normalized size (Size n_i)
            size_ni = traffic_ni / w_ixp
            total_size_N += size_ni

            temp_data.append(
                {
                    "id": node.id,
                    "name": node.name,
                    "traffic_ni": traffic_ni,
                    "size_ni": size_ni,
                }
            )

        # Calculate shares and leaving traffic
        stats: Dict[int, Dict[str, float]] = {}
        for item in temp_data:
            share_pct: float = (
                item["size_ni"] / total_size_N if total_size_N > 0 else 0.0
            )
            traffic_leaving: float = item["traffic_ni"] * (1.0 - share_pct)

            stats[item["id"]] = {
                "share_pct": share_pct,
                "traffic_leaving": traffic_leaving,
                "name": item["name"],
            }

        return stats, total_size_N

    @staticmethod
    def gravitational(topology: "Topology", rate: float = 0.015) -> NDArray[np.float64]:
        """
        Generate traffic matrix using the gravitational model.

        Traffic between nodes i and j is proportional to their populations:
        T(i,j) = K * Pop_i * Pop_j

        Parameters
        ----------
        topology : Topology
            The network topology.
        rate : float
            Traffic rate per population unit (default: 0.015 Gbps per capita)

        Returns
        -------
        numpy.ndarray
            Traffic matrix where matrix[i][j] is traffic from node i to node j (Gbps).
            Shape: (n_nodes, n_nodes)
        """
        nodes = list(topology.nodes)
        n = len(nodes)

        if n == 0:
            return np.array([], dtype=np.float64)

        K = TrafficMatrix._get_gravitational_k(topology, rate)
        if K == 0:
            return np.zeros((n, n), dtype=np.float64)

        matrix = np.zeros((n, n), dtype=np.float64)

        for i, node_i in enumerate(nodes):
            for j, node_j in enumerate(nodes):
                if i != j:
                    matrix[i, j] = K * node_i.pop * node_j.pop

        return matrix

    @staticmethod
    def dc_ixp(topology: "Topology") -> NDArray[np.float64]:
        """
        Generate traffic matrix using the DC/IXP model.

        Traffic depends on node degrees and the difference between DC and IXP resources:
        - If combined degree > 2*avg_degree: T(i,j) = 2*C(N,2)*delta_i*delta_j
        - Otherwise: T(i,j) = N*delta_i*delta_j

        where N = degree_i + degree_j, delta_i = |DC_i - IXP_i|

        Parameters
        ----------
        topology : Topology
            The network topology.

        Returns
        -------
        numpy.ndarray
            Traffic matrix where matrix[i][j] is traffic from node i to node j (Gbps).
            Shape: (n_nodes, n_nodes)
        """
        nodes = list(topology.nodes)
        n = len(nodes)

        if n == 0:
            return np.array([], dtype=np.float64)

        degrees = TrafficMatrix._calculate_node_degrees(topology)
        avg_degree = sum(degrees.values()) / n

        matrix = np.zeros((n, n), dtype=np.float64)

        for i, node_i in enumerate(nodes):
            for j, node_j in enumerate(nodes):
                if i != j:
                    N = degrees[node_i.id] + degrees[node_j.id]
                    delta_i = abs(node_i.dc - node_i.ixp)
                    delta_j = abs(node_j.dc - node_j.ixp)

                    if N > 2 * avg_degree:
                        if N < 2:
                            traffic = 0.0
                        else:
                            traffic = 2 * math.comb(N, 2) * delta_i * delta_j
                    else:
                        traffic = N * delta_i * delta_j

                    matrix[i, j] = traffic

        return matrix

    @staticmethod
    def distribution_probability(
        topology: "Topology",
        w_pop: float = 0.015,
        w_dc: float = 400.0,
        w_ixp: float = 2857.0,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 1.0,
    ) -> NDArray[np.float64]:
        """
        Generate traffic matrix using the distribution probability model.

        Traffic from node i to j is distributed proportionally based on
        resource shares and leaving traffic:
        T(i,j) = traffic_leaving_i * (share_j / (1 - share_i))

        Parameters
        ----------
        topology : Topology
            The network topology.
        w_pop : float
            Weight for population (Gbps per capita, default: 0.015)
        w_dc : float
            Weight for datacenter capacity (Gbps per DC, default: 400)
        w_ixp : float
            Weight for IXP capacity (Gbps per IXP, default: 2857)
        alpha : float
            Proportion of population data to use in the formula (default: 1.0).
            Controls what fraction of pop attribute is considered.
            Value of 1.0 uses all population data (equal importance with beta=1.0, gamma=1.0).
        beta : float
            Proportion of datacenter data to use in the formula (default: 1.0).
            Controls what fraction of dc attribute is considered.
            Value of 1.0 uses all datacenter data.
        gamma : float
            Proportion of IXP data to use in the formula (default: 1.0).
            Controls what fraction of ixp attribute is considered.
            Value of 1.0 uses all IXP data.

        Returns
        -------
        numpy.ndarray
            Traffic matrix where matrix[i][j] is traffic from node i to node j (Gbps).
            Shape: (n_nodes, n_nodes)

        Examples
        --------
        >>> # Equal importance: use all attributes fully
        >>> matrix = TrafficMatrix.distribution_probability(topology, alpha=1.0, beta=1.0, gamma=1.0)
        >>> # Use 50% of each attribute
        >>> matrix = TrafficMatrix.distribution_probability(topology, alpha=0.5, beta=0.5, gamma=0.5)
        >>> # Emphasize IXP: use 30% pop/dc, 100% IXP
        >>> matrix = TrafficMatrix.distribution_probability(topology, alpha=0.3, beta=0.3, gamma=1.0)
        """
        nodes = list(topology.nodes)
        n = len(nodes)

        if n == 0:
            return np.array([], dtype=np.float64)

        stats_lookup, total_size_N = TrafficMatrix._pre_calculate_metrics(
            topology, w_pop, w_dc, w_ixp, alpha, beta, gamma
        )

        if total_size_N == 0:
            return np.zeros((n, n), dtype=np.float64)

        matrix = np.zeros((n, n), dtype=np.float64)

        for i, node_i in enumerate(nodes):
            stats_i = stats_lookup[node_i.id]

            for j, node_j in enumerate(nodes):
                if i != j:
                    stats_j = stats_lookup[node_j.id]

                    traffic_leaving_i = stats_i["traffic_leaving"]
                    share_i = stats_i["share_pct"]
                    share_j = stats_j["share_pct"]

                    # Avoid division by zero
                    if share_i >= 1.0:
                        traffic = 0.0
                    else:
                        distribution_factor = share_j / (1.0 - share_i)
                        traffic = traffic_leaving_i * distribution_factor

                    matrix[i, j] = traffic

        return matrix

    @staticmethod
    def to_csv(
        matrix: NDArray[np.float64], topology: "Topology", filename: str
    ) -> None:
        """
        Export traffic matrix to CSV file.

        Parameters
        ----------
        matrix : numpy.ndarray
            Traffic matrix as numpy array
        topology : Topology
            The topology (needed to get node IDs for labels)
        filename : str
            Output CSV filename
        """
        if matrix.size == 0:
            return

        node_ids = [node.id for node in topology.nodes]
        n = len(node_ids)

        with open(filename, "w") as f:
            # Header
            f.write("src/dst," + ",".join(map(str, node_ids)) + "\n")

            # Rows
            for i in range(n):
                row = [str(node_ids[i])]
                for j in range(n):
                    row.append(f"{matrix[i, j]:.2f}")
                f.write(",".join(row) + "\n")

    @staticmethod
    def to_json(
        matrix: NDArray[np.float64],
        topology: "Topology",
        filename: str,
    ) -> None:
        """
        Export traffic matrix to JSON file.

        The JSON format is a list of traffic demands between node pairs,
        using node names and the 'required' field for traffic values.

        Parameters
        ----------
        matrix : numpy.ndarray
            Traffic matrix as numpy array
        topology : Topology
            The topology (needed to get node information)
        filename : str
            Output JSON filename

        Notes
        -----
        The output JSON structure is a list of demands:
        [
            {"src": "Node_A", "dst": "Node_B", "required": 10},
            {"src": "Node_A", "dst": "Node_C", "required": 15},
            ...
        ]
        Only non-zero traffic demands are included.
        """
        if matrix.size == 0:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
            return

        # Create a mapping from node id to node name
        node_map = {node.id: node.name for node in topology.nodes}
        node_ids = [node.id for node in topology.nodes]
        n = len(node_ids)

        # Build demands list (only non-zero values)
        demands_list: List[Dict[str, Any]] = []
        for i in range(n):
            for j in range(n):
                traffic = float(matrix[i, j])
                if traffic > 0:  # Only include non-zero traffic
                    demands_list.append(
                        {
                            "src": node_map[node_ids[i]],
                            "dst": node_map[node_ids[j]],
                            "required": round(traffic, 2),
                        }
                    )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(demands_list, f, indent=4, ensure_ascii=False)

    @staticmethod
    def multiperiod(
        base_matrix: NDArray[np.float64],
        num_periods: int = 10,
        base_growth_rate: float = 0.10,
        random_variation: float = 0.02,
        seed: int | None = None,
    ) -> NDArray[np.float64]:
        """
        Generate multi-period traffic matrices with growth over time.

        This method generates traffic matrices for multiple periods (e.g., years),
        applying a base growth rate plus random variation to each period.

        Parameters
        ----------
        base_matrix : numpy.ndarray
            Initial traffic matrix (period 0) as a 2D numpy array.
            Should be generated using one of the traffic generation methods
            (gravitational, dc_ixp, or distribution_probability).
        num_periods : int
            Number of periods to generate (default: 10).
        base_growth_rate : float
            Base yearly growth rate as decimal (default: 0.10 for 10%).
        random_variation : float
            Standard deviation for random growth variation (default: 0.02 for 2% std).
            Variation is sampled from a normal distribution N(0, random_variation).
        seed : int or None
            Random seed for reproducibility (default: None).

        Returns
        -------
        numpy.ndarray
            3D array of shape (num_periods, n_nodes, n_nodes) where:
            - First dimension is the period index
            - matrix[p][i][j] is traffic from node i to node j in period p (Gbps)

        Examples
        --------
        >>> # First generate a base traffic matrix
        >>> base_matrix = TrafficMatrix.gravitational(topology, rate=0.015)
        >>>
        >>> # Generate 10 periods with 10% base growth and 2% std variation
        >>> matrices = TrafficMatrix.multiperiod(
        ...     base_matrix,
        ...     num_periods=10,
        ...     base_growth_rate=0.10,
        ...     random_variation=0.02,
        ...     seed=42
        ... )
        >>> # Access period 5 matrix
        >>> period_5_matrix = matrices[5]

        >>> # Using DC/IXP model as base
        >>> base_matrix = TrafficMatrix.dc_ixp(topology)
        >>> matrices = TrafficMatrix.multiperiod(
        ...     base_matrix,
        ...     num_periods=5,
        ...     base_growth_rate=0.08,
        ...     random_variation=0.03
        ... )

        Notes
        -----
        The growth is compounded: each period multiplies the previous period's
        traffic by (1 + growth_rate), where growth_rate = base_growth_rate + variation,
        and variation is sampled from a normal distribution N(0, random_variation).
        """
        if num_periods < 1:
            raise ValueError("num_periods must be at least 1")

        if base_growth_rate < 0:
            raise ValueError("base_growth_rate must be non-negative")

        if random_variation < 0:
            raise ValueError("random_variation must be non-negative")

        if base_matrix.size == 0:
            return np.array([], dtype=np.float64)

        if base_matrix.ndim != 2:
            raise ValueError("base_matrix must be a 2D array")

        if base_matrix.shape[0] != base_matrix.shape[1]:
            raise ValueError("base_matrix must be square (n_nodes x n_nodes)")

        # Set random seed for reproducibility
        rng = np.random.default_rng(seed)

        # Initialize result array
        n_nodes = base_matrix.shape[0]
        result = np.zeros((num_periods, n_nodes, n_nodes), dtype=np.float64)

        # First period uses base matrix
        result[0] = base_matrix.copy()

        # Generate subsequent periods with growth
        for period in range(1, num_periods):
            # Calculate growth rate with random variation
            # Random variation is normally distributed with std = random_variation
            variation = rng.normal(0, random_variation)
            period_growth_rate = base_growth_rate + variation

            # Apply growth to previous period
            growth_factor = 1.0 + period_growth_rate
            result[period] = result[period - 1] * growth_factor

        return result
