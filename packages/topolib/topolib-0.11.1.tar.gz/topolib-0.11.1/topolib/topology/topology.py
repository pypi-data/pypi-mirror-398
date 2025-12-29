"""
Topology class for optical network topologies.

This module defines the Topology class, representing a network topology with nodes and links,
and providing an adjacency matrix using numpy.

This file uses NetworkX (BSD 3-Clause License):
https://github.com/networkx/networkx/blob/main/LICENSE.txt
"""

from __future__ import annotations

from typing import List, Optional, Any
from numpy.typing import NDArray


# Standard library imports
import json
import csv
from pathlib import Path

# Third-party imports
import numpy as np
import networkx as nx
import jsonschema

# Local imports
from topolib.elements.node import Node
from topolib.elements.link import Link


class Topology:
    """
    Represents a network topology with nodes and links.

    :param nodes: Initial list of nodes (optional).
    :type nodes: list[topolib.elements.node.Node] or None
    :param links: Initial list of links (optional).
    :type links: list[topolib.elements.link.Link] or None

    :ivar nodes: List of nodes in the topology.
    :vartype nodes: list[Node]
    :ivar links: List of links in the topology.
    :vartype links: list[Link]

    **Examples**
        >>> from topolib.elements.node import Node
        >>> from topolib.elements.link import Link
        >>> from topolib.topology import Topology
        >>> n1 = Node(1, "A", 0.0, 0.0)
        >>> n2 = Node(2, "B", 1.0, 1.0)
        >>> l1 = Link(1, n1, n2, 10.0)
        >>> topo = Topology(nodes=[n1, n2], links=[l1])
        >>> topo.adjacency_matrix()
        array([[0, 1],
               [1, 0]])
    """

    def __init__(
        self,
        nodes: Optional[List[Node]] = None,
        links: Optional[List[Link]] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize a Topology object.

        :param nodes: Initial list of nodes (optional).
        :type nodes: list[topolib.elements.node.Node] or None
        :param links: Initial list of links (optional).
        :type links: list[topolib.elements.link.Link] or None
        :param name: Name of the topology (optional).
        :type name: str or None
        """
        self.nodes = nodes if nodes is not None else []
        self.links = links if links is not None else []
        self.name = name
        # Internal NetworkX graph for algorithms and visualization
        self._graph: nx.DiGraph[Any] = nx.DiGraph()
        for node in self.nodes:
            self._graph.add_node(node.id, node=node)
        for link in self.links:
            self._graph.add_edge(link.source.id, link.target.id, link=link)

    @property
    def graph(self) -> nx.DiGraph[Any]:
        """
        Return the internal NetworkX directed graph representation.

        :return: NetworkX directed graph with nodes and edges.
        :rtype: networkx.DiGraph
        """
        return self._graph

    @classmethod
    def from_json(cls, json_path: str) -> "Topology":
        """
        Create a Topology object from a JSON file.

        :param json_path: Path to the JSON file containing the topology.
        :type json_path: str
        :return: Topology instance loaded from the file.
        :rtype: Topology
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validation schema for the assets JSON format
        topology_schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "weight": {"type": "number"},
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"},
                            "pop": {"type": "integer"},
                            "DC": {"type": "integer"},
                            "IXP": {"type": "integer"},
                        },
                        "required": ["id", "name", "latitude", "longitude"],
                    },
                },
                "links": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "src": {"type": "integer"},
                            "dst": {"type": "integer"},
                            "length": {"type": "number"},
                        },
                        "required": ["id", "src", "dst", "length"],
                    },
                },
            },
            "required": ["nodes", "links"],
        }
        try:
            jsonschema.validate(instance=data, schema=topology_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Invalid topology JSON format: {e.message}")
        nodes = [
            Node(
                n["id"],
                n["name"],
                n["latitude"],
                n["longitude"],
                n.get("weight", 0),
                n.get("pop", 0),
                n.get("dc", n.get("DC", 0)),
                n.get("ixp", n.get("IXP", 0)),
            )
            for n in data["nodes"]
        ]
        # Crear un dict para mapear id a Node
        node_dict = {n.id: n for n in nodes}
        links = [
            Link(l["id"], node_dict[l["src"]], node_dict[l["dst"]], l["length"])
            for l in data["links"]
        ]
        name = data.get("name", None)
        return cls(nodes=nodes, links=links, name=name)

    def add_node(self, node: Node) -> None:
        """
        Add a node to the topology.

        :param node: Node to add.
        :type node: Node
        """
        self.nodes.append(node)
        self._graph.add_node(node.id, node=node)

    def add_link(self, link: Link) -> None:
        """
        Add a link to the topology.

        :param link: Link to add.
        :type link: Link
        """
        self.links.append(link)
        self._graph.add_edge(link.source.id, link.target.id, link=link)

    def remove_node(self, node_id: int) -> None:
        """
        Remove a node and all its links by node id.

        :param node_id: ID of the node to remove.
        :type node_id: int
        """
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.links = [
            l for l in self.links if l.source.id != node_id and l.target.id != node_id
        ]
        self._graph.remove_node(node_id)

    def remove_link(self, link_id: int) -> None:
        """
        Remove a link by its id.

        :param link_id: ID of the link to remove.
        :type link_id: int
        """
        # Find the link and remove from graph
        link = next((l for l in self.links if l.id == link_id), None)
        if link:
            self._graph.remove_edge(link.source.id, link.target.id)
        self.links = [l for l in self.links if l.id != link_id]

    def adjacency_matrix(self) -> NDArray[np.int_]:
        """
        Return the adjacency matrix of the topology as a numpy array.

        :return: Adjacency matrix (1 if connected, 0 otherwise).
        :rtype: numpy.ndarray

        **Example**
            >>> topo.adjacency_matrix()
            array([[0, 1],
                   [1, 0]])
        """
        # Usa NetworkX para obtener la matriz de adyacencia
        if not self.nodes:
            return np.zeros((0, 0), dtype=int)
        node_ids = [n.id for n in self.nodes]
        mat = nx.to_numpy_array(self._graph, nodelist=node_ids, dtype=np.int_)  # type: ignore[arg-type]
        return mat

    def export_to_json(self, file_path: str) -> None:
        """
        Export the current topology to the JSON format used in the assets folder.

        :param file_path: Path where the JSON file will be saved.
        :type file_path: str

        Example usage::

            topo.export_to_json("/path/output.json")

        Example output format::

            {
                "name": "Abilene",
                "nodes": [
                    {
                        "id": 0,
                        "name": "Seattle",
                        ...
                    }
                ],
                "links": [
                    {
                        "id": 0,
                        "src": 0,
                        "dst": 1,
                        "length": 1482.26
                    }
                ]
            }
        """
        nodes_list: list[dict[str, Any]] = []
        for n in self.nodes:
            node_dict: dict[str, Any] = {
                "id": n.id,
                "name": getattr(n, "name", None),
                "weight": getattr(n, "weight", 0),
                "latitude": getattr(n, "latitude", None),
                "longitude": getattr(n, "longitude", None),
                "pop": getattr(n, "pop", 0),
                "DC": getattr(n, "dc", getattr(n, "DC", 0)),
                "IXP": getattr(n, "ixp", getattr(n, "IXP", 0)),
            }
            nodes_list.append(node_dict)
        links_list: list[dict[str, Any]] = []
        for l in self.links:
            link_dict: dict[str, Any] = {
                "id": l.id,
                "src": l.source.id,
                "dst": l.target.id,
                "length": getattr(l, "length", None),
            }
            links_list.append(link_dict)
        data: dict[str, Any] = {
            "name": self.name if self.name else "Topology",
            "nodes": nodes_list,
            "links": links_list,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_to_csv(self, filename_prefix: str) -> None:
        """
        Export the topology to two CSV files: one for nodes and one for links.
        The files will be named as <filename_prefix>_nodes.csv and <filename_prefix>_links.csv.

        :param filename_prefix: Prefix for the output files (e.g., 'topology1').
        :type filename_prefix: str

        Example:
            >>> topo.export_to_csv("mytopo")
            # Generates 'mytopo_nodes.csv' and 'mytopo_links.csv'
        """
        # Export nodes
        nodes_path = f"{filename_prefix}_nodes.csv"
        with open(nodes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(
                ["id", "name", "weight", "latitude", "longitude", "pop", "DC", "IXP"]
            )
            for n in self.nodes:
                writer.writerow(
                    [
                        n.id,
                        getattr(n, "name", None),
                        getattr(n, "weight", 0),
                        getattr(n, "latitude", None),
                        getattr(n, "longitude", None),
                        getattr(n, "pop", 0),
                        getattr(n, "dc", getattr(n, "DC", 0)),
                        getattr(n, "ixp", getattr(n, "IXP", 0)),
                    ]
                )
        # Export links
        links_path = f"{filename_prefix}_links.csv"
        with open(links_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "src", "dst", "length"])
            for l in self.links:
                writer.writerow(
                    [
                        l.id,
                        l.source.id,
                        l.target.id,
                        getattr(l, "length", None),
                    ]
                )

    def export_to_flexnetsim_json(self, file_path: str, slots: int) -> None:
        """
        Export the current topology to a JSON file compatible with Flex Net Sim.

        :param file_path: Path where the JSON file will be saved.
        :type file_path: str
        :param slots: Number of slots for each link.
        :type slots: int

        The generated format includes the following fields:
        - alias: short name of the topology (uses self.name if available)
        - name: full name of the topology (uses self.name if available)
        - nodes: list of nodes with 'id' field
        - links: list of links with id, src, dst, length, slots
        """
        alias = self.name if self.name else "Topology"
        name = self.name if self.name else "Topology"
        nodes_list = [{"id": n.id} for n in self.nodes]
        links_list: list[dict[str, Any]] = []
        for l in self.links:
            link_dict: dict[str, Any] = {
                "id": l.id,
                "src": l.source.id,
                "dst": l.target.id,
                "length": getattr(l, "length", None),
                "slots": slots,
            }
            links_list.append(link_dict)
        data: dict[str, Any] = {
            "alias": alias,
            "name": name,
            "nodes": nodes_list,
            "links": links_list,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_to_flexnetsim_ksp_json(self, file_path: str, k: int = 3) -> None:
        """
        Export the k-shortest paths between all node pairs to a JSON file compatible with Flex Net Sim.

        :param file_path: Path where the JSON file will be saved.
        :type file_path: str
        :param k: Number of shortest paths to compute for each node pair (default: 3).
        :type k: int

        Example output format::

            {
                "name": self.name,
                "alias": self.name,
                "routes": [
                    {"src": <id>, "dst": <id>, "paths": [[id, ...], ...]},
                    ...
                ]
            }
        """

        # Build a weighted graph using link length as edge weight
        G: nx.DiGraph[int] = nx.DiGraph()
        for l in self.links:
            G.add_edge(l.source.id, l.target.id, weight=getattr(l, "length", 1))  # type: ignore[arg-type]
        routes: list[dict[str, Any]] = []
        node_ids = [n.id for n in self.nodes]
        for src in node_ids:
            for dst in node_ids:
                if src == dst:
                    continue
                try:
                    # Compute k shortest paths using link length as weight
                    paths_gen = nx.shortest_simple_paths(G, src, dst, weight="weight")  # type: ignore[arg-type]
                    paths: list[list[int]] = []
                    for i, path in enumerate(paths_gen):
                        if i >= k:
                            break
                        paths.append(path)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    paths = []
                routes.append({"src": src, "dst": dst, "paths": paths})
        data: dict[str, Any] = {
            "name": self.name if self.name else "Topology",
            "alias": self.name if self.name else "Topology",
            "routes": routes,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @classmethod
    def list_available_topologies(cls) -> list[dict[str, Any]]:
        """
        List available topologies in the assets folder.

        Returns a list of dictionaries with keys:
        - 'name': topology name (filename without extension)
        - 'nodes': number of nodes
        - 'links': number of links

        :return: List of available topologies with metadata.
        :rtype: list[dict[str, Any]]
        """
        asset_dir = Path(__file__).parent.parent / "assets"
        result: list[dict[str, Any]] = []
        for json_path in asset_dir.glob("*.json"):
            try:
                topo = cls.from_json(str(json_path))
                result.append(
                    {
                        "name": json_path.stem,
                        "nodes": len(topo.nodes),
                        "links": len(topo.links),
                    }
                )
            except Exception:
                continue
        return result

    @staticmethod
    def load_default_topology(name: str) -> "Topology":
        """
        Load a default topology from the assets folder by name (filename without extension).

        :param name: Name of the topology asset (without .json extension)
        :type name: str
        :return: Topology instance loaded from the asset file
        :rtype: Topology
        :raises FileNotFoundError: If the asset file does not exist
        """
        asset_dir = Path(__file__).parent.parent / "assets"
        asset_path = asset_dir / f"{name}.json"
        if not asset_path.exists():
            raise FileNotFoundError(
                f"Topology asset '{name}.json' not found in assets directory."
            )
        return Topology.from_json(str(asset_path))
