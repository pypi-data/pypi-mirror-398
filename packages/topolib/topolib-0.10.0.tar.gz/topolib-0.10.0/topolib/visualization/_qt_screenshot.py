"""
Qt screenshot script for capturing maps as PNG images.

This module provides a standalone script that can be executed in a subprocess
to render HTML content and capture it as a PNG screenshot.
"""

import sys
import os
from pathlib import Path

# Suppress Qt warnings
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.webenginecontext.debug=false;qt.qpa.windows=false'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-logging --log-level=3'

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtCore import QUrl, QTimer, QEventLoop, Qt
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    from PyQt6.QtGui import QPixmap
except ImportError:
    print("ERROR: PyQt6 not installed. Install with: pip install PyQt6 PyQt6-WebEngine")
    sys.exit(1)


def capture_screenshot(html_path: str, output_path: str, width: int = 1920, height: int = 1080, wait_time: float = 1.0) -> None:
    """Capture a screenshot of an HTML file.
    
    :param html_path: Absolute path to the HTML file to render.
    :type html_path: str
    :param output_path: Path where the PNG screenshot will be saved.
    :type output_path: str
    :param width: Width of the screenshot in pixels.
    :type width: int
    :param height: Height of the screenshot in pixels.
    :type height: int
    :param wait_time: Time in seconds to wait for rendering before capture.
    :type wait_time: float
    """
    app = QApplication(sys.argv)
    
    # Create web view offscreen (no window displayed)
    web_view = QWebEngineView()
    web_view.setGeometry(0, 0, width, height)
    # Render offscreen without showing window
    web_view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    web_view.show()  # Trigger rendering without displaying
    
    # Configure settings
    settings = web_view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    
    def on_load_finished(ok):
        if ok:
            # Wait for Leaflet/JavaScript to fully render the map
            QTimer.singleShot(int(wait_time * 1000), capture)
    
    def capture():
        # Grab the rendered content
        pixmap = web_view.grab()
        pixmap.save(output_path, 'PNG')
        app.quit()
    
    web_view.loadFinished.connect(on_load_finished)
    
    # Load the HTML file
    web_view.load(QUrl.fromLocalFile(html_path))
    
    # Suppress output during execution
    null_fd = os.open(os.devnull, os.O_RDWR)
    save_stderr = os.dup(2)
    os.dup2(null_fd, 2)
    
    app.exec()
    
    # Restore stderr
    os.dup2(save_stderr, 2)
    os.close(null_fd)
    os.close(save_stderr)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python _qt_screenshot.py <html_path> <output_path> [width] [height] [wait_time]")
        sys.exit(1)
    
    html_path = sys.argv[1]
    output_path = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1920
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
    wait_time = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    
    if not Path(html_path).exists():
        print(f"ERROR: HTML file not found: {html_path}")
        sys.exit(1)
    
    try:
        capture_screenshot(html_path, output_path, width, height, wait_time)
    except Exception as e:
        print(f"ERROR: Failed to capture screenshot: {e}")
        sys.exit(1)
