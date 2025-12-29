"""
MapView class for visualizing network topologies.

This module provides visualization methods for Topology objects using Folium.
"""

from typing import Optional
import webbrowser
import tempfile
import os
import sys
import re
import urllib.request
import hashlib
import subprocess
from pathlib import Path
from topolib.topology import Topology
import folium
from folium import plugins
from topolib.elements.link import Link
from topolib.elements.node import Node
from . import _templates

# Global cache directory for downloaded resources
CACHE_DIR = Path.home() / '.topolib' / 'cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class MapView:
    """
    Provides interactive visualization methods for Topology objects using Folium.

    This class creates interactive HTML maps with OpenStreetMap tiles,
    displaying network nodes as clickable markers and links as lines between them.
    """

    def __init__(self, topology: Topology) -> None:
        """Create a MapView instance for a Topology.

        :param topology: Topology object to visualize.
        :type topology: topolib.topology.Topology
        """
        self.topology = topology
        self._map = None

    def _create_map(self, include_controls: bool = True) -> folium.Map:
        """Create a Folium map with the current topology.

        :param include_controls: Whether to include interactive controls (zoom, fullscreen, etc.).
        :type include_controls: bool
        :return: Folium Map object with nodes and links rendered.
        :rtype: folium.Map
        """
        # Get topology name
        topo_name = getattr(self.topology, "name", None) or "Topology"

        # Calculate map center
        if self.topology.nodes:
            avg_lat = sum(node.latitude for node in self.topology.nodes) / len(
                self.topology.nodes
            )
            avg_lon = sum(node.longitude for node in self.topology.nodes) / len(
                self.topology.nodes
            )
        else:
            avg_lat, avg_lon = 0, 0

        # Create base map using template configuration
        map_config = _templates.MAP_DEFAULT_CONFIG.copy()
        if not include_controls:
            map_config['zoom_control'] = False
            map_config['control_scale'] = False
        
        m = folium.Map(
            location=[avg_lat, avg_lon],
            **map_config
        )
        
        # Disable attribution if no controls
        if not include_controls:
            m.get_root().html.add_child(folium.Element("""
            <style>
                .leaflet-control-attribution {
                    display: none !important;
                }
                .leaflet-control-zoom {
                    display: none !important;
                }
                .leaflet-bar {
                    display: none !important;
                }
            </style>
            """))

        # Add title using template
        title_html = _templates.TITLE_TEMPLATE.format(title=topo_name)
        m.get_root().html.add_child(folium.Element(title_html))

        # Draw links first (so they appear below nodes)
        for link in self.topology.links:
            coords = [
                [link.source.latitude, link.source.longitude],
                [link.target.latitude, link.target.longitude],
            ]

            popup_text = _templates.format_link_popup(link)

            folium.PolyLine(
                coords,
                popup=folium.Popup(popup_text, max_width=300) if include_controls else None,
                **_templates.LINK_LINE_CONFIG
            ).add_to(m)

        # Draw nodes
        for node in self.topology.nodes:
            popup_html = _templates.format_node_popup(node)

            folium.CircleMarker(
                location=[node.latitude, node.longitude],
                popup=folium.Popup(popup_html, max_width=300) if include_controls else None,
                tooltip=node.name if include_controls else None,
                **_templates.NODE_MARKER_CONFIG
            ).add_to(m)

        # Add interactive controls only if requested
        if include_controls:
            # Add fullscreen button
            plugins.Fullscreen().add_to(m)

            # Add measure control for distance measurement
            plugins.MeasureControl(position='topleft').add_to(m)

        self._map = m
        return m

    def show_map(self, mode: str = "window") -> None:
        """Display the interactive map in a web browser or GUI window.

        Creates an HTML map and displays it either in the system's default web browser
        or in an interactive PyQt window.

        The map includes:
        - Interactive nodes with clickable popups showing node information
        - Links between nodes with hover tooltips
        - Zoom and pan controls
        - Fullscreen mode
        - Distance measurement tool

        :param mode: Display mode - "window" opens in PyQt window, "browser" opens in web browser (default: "window").
        :type mode: str
        :raises ImportError: If mode="window" and PyQt6 is not installed.
        :returns: None
        """
        # Suppress Qt warnings early
        if mode == "window":
            os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.webenginecontext.debug=false;qt.qpa.windows=false'
            os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-logging --log-level=3'
        
        m = self._create_map()

        # Save to temporary HTML file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding='utf-8'
        ) as tmp:
            tmp_path = tmp.name
            m.save(tmp_path)

        # For window mode, embed external resources
        if mode == "window":
            self._embed_resources(tmp_path)
            self._show_in_window(tmp_path)
        else:
            # Try to open in default web browser
            try:
                webbrowser.open("file://" + os.path.abspath(tmp_path))
                print(
                    f"Map opened in browser. If it didn't open, access: file://{os.path.abspath(tmp_path)}")
            except Exception as e:
                print(f"Could not open browser: {e}")
                print(f"You can manually open: {tmp_path}")

    def _embed_resources(self, html_path: str) -> None:
        """Embed external CSS and JS resources directly into the HTML file.

        :param html_path: Path to the HTML file to modify.
        :type html_path: str
        """
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Find all external script and link tags
        script_pattern = r'<script src="(https?://[^"]+)"><\/script>'
        link_pattern = r'<link rel="stylesheet" href="(https?://[^"]+)"[^>]*/?>'

        # Download and embed scripts with caching
        def replace_script(match):
            url = match.group(1)
            try:
                content = self._get_cached_resource(url)
                return f'<script>{content}</script>'
            except Exception as e:
                print(f"Warning: Could not download {url}: {e}")
                return match.group(0)  # Keep original if download fails

        # Download and embed stylesheets with caching
        def replace_link(match):
            url = match.group(1)
            try:
                content = self._get_cached_resource(url)
                return f'<style>{content}</style>'
            except Exception as e:
                print(f"Warning: Could not download {url}: {e}")
                return match.group(0)  # Keep original if download fails

        html_content = re.sub(script_pattern, replace_script, html_content)
        html_content = re.sub(link_pattern, replace_link, html_content)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _get_cached_resource(self, url: str) -> str:
        """Get resource from cache or download if not cached.

        :param url: URL of the resource to download.
        :type url: str
        :return: Content of the resource.
        :rtype: str
        """
        # Create a hash of the URL to use as filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_file = CACHE_DIR / url_hash
        
        # Check if cached
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Download and cache
        print(f"Downloading: {url}")
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode('utf-8')
        
        # Save to cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return content

    def _show_in_window(self, html_path: str) -> None:
        """Display the map in a PyQt window.

        :param html_path: Path to the HTML file to display.
        :type html_path: str
        :raises ImportError: If PyQt6 is not installed.
        """
        # Get the path to the Qt window script
        qt_script = Path(__file__).parent / '_qt_window.py'
        
        # Run the Qt window in a subprocess for isolation
        window_title = self.topology.name or 'Topology Map'
        subprocess.run([sys.executable, str(qt_script), html_path, window_title], check=True)

    def export_html(self, filename: str) -> None:
        """Export the map as a standalone HTML file.

        :param filename: Output HTML file path.
        :type filename: str
        """
        m = self._create_map()
        m.save(filename)

    def export_map_png(self, filename: str, width: int = 1920, height: int = 1080, wait_time: float = 1.0) -> None:
        """Export the map as a PNG image using PyQt6.

        :param filename: Output PNG file path.
        :type filename: str
        :param width: Width of the exported image in pixels (default: 1920).
        :type width: int
        :param height: Height of the exported image in pixels (default: 1080).
        :type height: int
        :param wait_time: Time in seconds to wait for map rendering before capture (default: 1.0).
        :type wait_time: float
        :raises ImportError: If PyQt6 is not installed.
        """
        # Create map without interactive controls for clean export
        m = self._create_map(include_controls=False)

        # Save to temporary HTML file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding='utf-8'
        ) as tmp:
            tmp_path = tmp.name
            m.save(tmp_path)

        # Embed resources for offline rendering
        self._embed_resources(tmp_path)

        # Get the path to the screenshot script
        screenshot_script = Path(__file__).parent / '_qt_screenshot.py'
        
        # Run the screenshot script in a subprocess
        try:
            subprocess.run(
                [sys.executable, str(screenshot_script), tmp_path, filename, str(width), str(height), str(wait_time)], 
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to capture screenshot: {e.stderr}")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
