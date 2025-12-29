"""
Path class for representing a sequence of nodes and links in a topology.
"""

from typing import List, Any


class Path:
    """
    Represents a path through the network topology as an ordered sequence of nodes and links.

    Parameters
    ----------
    nodes : list
        Ordered list of node objects in the path.
    links : list
        Ordered list of link objects in the path (len(links) == len(nodes) - 1).

    Raises
    ------
    ValueError
        If the number of nodes and links is inconsistent or empty.

    Attributes
    ----------
    nodes : list
        Ordered list of nodes in the path.
    links : list
        Ordered list of links in the path.

    Examples
    --------
    >>> nodes = [Node(1), Node(2), Node(3)]
    >>> links = [Link('a'), Link('b')]
    >>> path = Path(nodes, links)
    >>> path.length()
    2
    >>> path.endpoints()
    (Node(1), Node(3))
    """

    def __init__(self, nodes: List[Any], links: List[Any]):
        if not nodes or not links:
            raise ValueError("A path must have at least one node and one link.")
        if len(nodes) != len(links) + 1:
            raise ValueError("Number of nodes must be one more than number of links.")
        self.nodes = nodes
        self.links = links

    def length(self) -> int:
        """
        Return the number of links in the path.

        Returns
        -------
        int
            Number of links in the path.
        """
        return len(self.links)

    def hop_count(self) -> int:
        """
        Return the number of hops (links) in the path.

        Returns
        -------
        int
            Number of hops (links) in the path.
        """
        return self.length()

    def endpoints(self):
        """
        Return the source and target nodes of the path as a tuple.

        Returns
        -------
        tuple
            (source_node, target_node)
        """
        return (self.nodes[0], self.nodes[-1])

    def __repr__(self):
        return f"Path(nodes={self.nodes}, links={self.links})"
