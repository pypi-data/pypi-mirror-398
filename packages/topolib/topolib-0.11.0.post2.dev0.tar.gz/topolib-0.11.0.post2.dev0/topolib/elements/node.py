"""
Node class for optical network topologies.

This module defines the Node class, representing a network node with geographic coordinates.
"""

from typing import Tuple


class Node:
    """
    Represents a node in an optical network topology.

    :param id: Unique identifier for the node.
    :type id: int
    :param name: Name of the node.
    :type name: str
    :param latitude: Latitude coordinate of the node.
    :type latitude: float
    :param longitude: Longitude coordinate of the node.
    :type longitude: float
    :param weight: Node weight (optional, default 0).
    :type weight: float or int
    :param pop: Node population (optional, default 0).
    :type pop: int
    :param dc: Datacenter (DC) value for the node (optional, default 0).
    :type dc: int
    :param ixp: IXP (Internet Exchange Point) value for the node (optional, default 0).
    :type ixp: int
    """

    def __init__(
        self,
        id: int,
        name: str,
        latitude: float,
        longitude: float,
        weight: float = 0,
        pop: int = 0,
        dc: int = 0,
        ixp: int = 0,
    ):
        self._id = id
        self._name = name
        self._latitude = latitude
        self._longitude = longitude
        self._weight = weight
        self._pop = pop
        self._dc = dc
        self._ixp = ixp

    @property
    def dc(self) -> int:
        """
        Get the datacenter (DC) count or value for the node.

        :return: Node DC value.
        :rtype: int
        """
        return self._dc

    @dc.setter
    def dc(self, value: int) -> None:
        """
        Set the datacenter (DC) value for the node.

        :param value: Node DC value.
        :type value: int
        """
        self._dc = value

    @property
    def ixp(self) -> int:
        """
        Get the IXP (Internet Exchange Point) count or value for the node.

        :return: Node IXP value.
        :rtype: int
        """
        return self._ixp

    @ixp.setter
    def ixp(self, value: int) -> None:
        """
        Set the IXP (Internet Exchange Point) value for the node.

        :param value: Node IXP value.
        :type value: int
        """
        self._ixp = value

    @property
    def id(self) -> int:
        """
        Get the unique identifier of the node.

        :return: Node ID.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        """
        Set the unique identifier of the node.

        :param value: Node ID.
        :type value: int
        """
        self._id = value

    @property
    def name(self) -> str:
        """
        Get the name of the node.

        :return: Node name.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Set the name of the node.

        :param value: Node name.
        :type value: str
        """
        self._name = value

    @property
    def latitude(self) -> float:
        """
        Get the latitude coordinate of the node.

        :return: Latitude value.
        :rtype: float
        """
        return self._latitude

    @latitude.setter
    def latitude(self, value: float) -> None:
        """
        Set the latitude coordinate of the node.

        :param value: Latitude value.
        :type value: float
        """
        self._latitude = value

    @property
    def longitude(self) -> float:
        """
        Get the longitude coordinate of the node.

        :return: Longitude value.
        :rtype: float
        """
        return self._longitude

    @longitude.setter
    def longitude(self, value: float) -> None:
        """
        Set the longitude coordinate of the node.

        :param value: Longitude value.
        :type value: float
        """
        self._longitude = value

    @property
    def weight(self) -> float:
        """
        Get the weight of the node.

        :return: Node weight.
        :rtype: float
        """
        return self._weight

    @weight.setter
    def weight(self, value: float) -> None:
        """
        Set the weight of the node.

        :param value: Node weight.
        :type value: float
        """
        self._weight = value

    @property
    def pop(self) -> int:
        """
        Get the population of the node.

        :return: Node population.
        :rtype: int
        """
        return self._pop

    @pop.setter
    def pop(self, value: int) -> None:
        """
        Set the population of the node.

        :param value: Node population.
        :type value: int
        """
        self._pop = value

    def coordinates(self) -> Tuple[float, float]:
        """
        Returns the (latitude, longitude) coordinates of the node.

        :return: Tuple containing latitude and longitude.
        :rtype: Tuple[float, float]
        """
        return self._latitude, self._longitude

    def __repr__(self) -> str:
        """Return a concise representation of the Node.

        Includes id, name, latitude, longitude and additional attributes.
        """
        return (
            f"Node(id={self._id}, name={self._name!r}, latitude={self._latitude}, "
            f"longitude={self._longitude}, weight={self._weight}, pop={self._pop}, "
            f"dc={self._dc}, ixp={self._ixp})"
        )
