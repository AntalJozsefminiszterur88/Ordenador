"""Application entry point for the Ordenador assistant GUI."""

import sys

from PySide6.QtWidgets import QApplication

from src.gui import MainWindow


def main() -> None:
    """Start the Qt application and show the main window."""

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
