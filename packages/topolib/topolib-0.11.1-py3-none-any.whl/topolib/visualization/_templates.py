"""
HTML templates for MapView visualization.

This module contains HTML/CSS templates used to render topology maps.
"""

# Template for the topology title overlay
TITLE_TEMPLATE = """
<div style="position: fixed; 
            top: 10px; left: 50px; width: 300px; height: 50px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:16px; font-weight: bold; padding: 10px">
    {title}
</div>
"""

# Template for node popup information
NODE_POPUP_TEMPLATE = """
<div style="width: 200px">
    <h4>{name}</h4>
    <b>ID:</b> {id}<br>
    <b>Latitude:</b> {latitude:.6f}<br>
    <b>Longitude:</b> {longitude:.6f}<br>
    {optional_attributes}
</div>
"""

# Template for link popup information
LINK_POPUP_TEMPLATE = """
<b>Link {id}</b><br>
From: {source_name} (ID: {source_id})<br>
To: {target_name} (ID: {target_id})<br>
Length: {length:.2f} km
"""

# Node marker style configuration
NODE_MARKER_CONFIG = {
    'radius': 8,
    'color': 'blue',
    'fill': True,
    'fillColor': 'blue',
    'fillOpacity': 0.7
}

# Link line style configuration
LINK_LINE_CONFIG = {
    'color': 'gray',
    'weight': 2,
    'opacity': 0.7
}

# Map default configuration
MAP_DEFAULT_CONFIG = {
    'zoom_start': 5,
    'tiles': 'OpenStreetMap',
    'control_scale': True
}


def format_node_popup(node) -> str:
    """Format a node's information for popup display.
    
    :param node: Node object to format.
    :return: Formatted HTML string.
    :rtype: str
    """
    optional_attrs = []
    
    if hasattr(node, 'weight') and node.weight:
        optional_attrs.append(f"<b>Weight:</b> {node.weight}<br>")
    if hasattr(node, 'pop') and node.pop:
        optional_attrs.append(f"<b>Population:</b> {node.pop:,}<br>")
    if hasattr(node, 'dc') and node.dc:
        optional_attrs.append(f"<b>DC:</b> {node.dc}<br>")
    if hasattr(node, 'ixp') and node.ixp:
        optional_attrs.append(f"<b>IXP:</b> {node.ixp}<br>")
    
    return NODE_POPUP_TEMPLATE.format(
        name=node.name,
        id=node.id,
        latitude=node.latitude,
        longitude=node.longitude,
        optional_attributes=''.join(optional_attrs)
    )


def format_link_popup(link) -> str:
    """Format a link's information for popup display.
    
    :param link: Link object to format.
    :return: Formatted HTML string.
    :rtype: str
    """
    return LINK_POPUP_TEMPLATE.format(
        id=link.id,
        source_name=link.source.name,
        source_id=link.source.id,
        target_name=link.target.name,
        target_id=link.target.id,
        length=link.length
    )
