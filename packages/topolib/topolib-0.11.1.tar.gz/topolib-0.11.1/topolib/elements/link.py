from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolib.elements.node import Node


class Link:
    """
    Represents a link between two nodes.

    Parameters
    ----------
    id : int
        Unique identifier for the link.
    source : :class:`topolib.elements.node.Node`
        Source node-like object (must have id, name, latitude, longitude).
    target : :class:`topolib.elements.node.Node`
        Target node-like object (must have id, name, latitude, longitude).
    length : float
        Length of the link (must be non-negative).

    Examples
    --------
    >>> link = Link(1, nodeA, nodeB, 10.5)
    >>> link.length
    """

    def __init__(self, id: int, source: "Node", target: "Node", length: float):
        self._id = id
        self.source = source
        self.target = target
        self.length = length

    @property
    def id(self) -> int:
        """
        int: Unique identifier for the link.
        """
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        """
        Set the link's unique identifier.
        """
        self._id = value

    @property
    def source(self) -> "Node":
        """
        :class:`topolib.elements.node.Node`: Source node of the link.
        """
        return self._source

    @source.setter
    def source(self, value: "Node") -> None:
        """
        Set the source node. Must have id, name, latitude, longitude.
        """
        required_attrs = ("id", "name", "latitude", "longitude")
        for attr in required_attrs:
            if not hasattr(value, attr):
                raise TypeError(f"source must behave like a Node (missing {attr})")
        self._source = value

    @property
    def target(self) -> "Node":
        """
        :class:`topolib.elements.node.Node`: Target node of the link.
        """
        return self._target

    @target.setter
    def target(self, value: "Node") -> None:
        """
        Set the target node. Must have id, name, latitude, longitude.
        """
        required_attrs = ("id", "name", "latitude", "longitude")
        for attr in required_attrs:
            if not hasattr(value, attr):
                raise TypeError(f"target must behave like a Node (missing {attr})")
        self._target = value

    @property
    def length(self) -> float:
        """
        float: Length of the link (non-negative).
        """
        return self._length

    @length.setter
    def length(self, value: float) -> None:
        """
        Set the length of the link. Must be a non-negative float.
        """
        try:
            numeric = float(value)
        except Exception:
            raise TypeError("length must be a numeric value")
        if numeric < 0:
            raise ValueError("length must be non-negative")
        self._length = numeric

    def endpoints(self):
        """
        Return the (source, target) nodes as a tuple.

        Returns
        -------
        tuple
            (source_node, target_node)
        """
        return self._source, self._target

    def __repr__(self) -> str:
        """
        Return a string representation of the Link.
        """
        return f"Link(id={self._id}, source={self._source.id} ({self.source.name}), target={self._target.id} ({self.target.name}), length={self._length})"
