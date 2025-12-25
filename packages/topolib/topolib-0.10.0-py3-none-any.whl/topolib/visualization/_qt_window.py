"""
Qt window script for displaying maps in isolated subprocess.

This module provides a standalone script that can be executed in a subprocess
to display HTML content in a PyQt6 window without interfering with the main process.
"""

import sys
import os

# Suppress Qt warnings
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.webenginecontext.debug=false;qt.qpa.windows=false'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-logging --log-level=3'

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtCore import QUrl
    from PyQt6.QtWebEngineCore import QWebEngineSettings
except ImportError:
    print("ERROR: PyQt6 not installed. Install with: pip install PyQt6 PyQt6-WebEngine")
    sys.exit(1)


class SuppressOutput:
    """Context manager to suppress stdout/stderr during Qt event loop."""
    
    def __enter__(self):
        self.null_fd = os.open(os.devnull, os.O_RDWR)
        self.save_stdout = os.dup(1)
        self.save_stderr = os.dup(2)
        os.dup2(self.null_fd, 1)
        os.dup2(self.null_fd, 2)
        return self
    
    def __exit__(self, *args):
        os.dup2(self.save_stdout, 1)
        os.dup2(self.save_stderr, 2)
        os.close(self.null_fd)
        os.close(self.save_stdout)
        os.close(self.save_stderr)


def show_html_in_window(html_path: str, window_title: str = "Map Viewer") -> None:
    """Display an HTML file in a PyQt6 window.
    
    :param html_path: Absolute path to the HTML file to display.
    :type html_path: str
    :param window_title: Title for the window.
    :type window_title: str
    """
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle(window_title)
    window.resize(1200, 800)

    web_view = QWebEngineView()
    settings = web_view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

    web_view.load(QUrl.fromLocalFile(html_path))
    window.setCentralWidget(web_view)
    window.show()

    with SuppressOutput():
        app.exec()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python _qt_window.py <html_path> [window_title]")
        sys.exit(1)
    
    html_path = sys.argv[1]
    window_title = sys.argv[2] if len(sys.argv) > 2 else "Map Viewer"
    
    show_html_in_window(html_path, window_title)
