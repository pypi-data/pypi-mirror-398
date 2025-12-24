"""
Main application entry point for MagPy GUI.
"""

import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from magpy.main_window import MainWindow


def main(filepath: Optional[str] = None) -> int:
    """
    Launch the MagPy application.

    Args:
        filepath: Optional audio file to open on startup.

    Returns:
        Application exit code.
    """
    # Enable high DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("MagPy")
    app.setOrganizationName("MagPy")
    app.setOrganizationDomain("bioamla.org")

    # Create main window
    window = MainWindow()

    # Open file if provided
    if filepath:
        window.load_file(filepath)
    elif len(sys.argv) > 1:
        window.load_file(sys.argv[1])

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
