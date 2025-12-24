"""Entry point for python -m photosortman or photosortman command"""
import sys
from PyQt6.QtWidgets import QApplication
from .photoman import PhotoSorterApp


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    
    # Create window - PhotoSorterApp doesn't take parameters
    # User will select folder through the UI
    window = PhotoSorterApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
