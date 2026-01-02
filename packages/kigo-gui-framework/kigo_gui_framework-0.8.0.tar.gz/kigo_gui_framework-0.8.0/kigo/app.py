import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

# Assuming the widgets module is still available
from .widgets import Label, Button, TextBox, Dropdown, Browser 

class App:
    """The main application window and entry point."""
    
    def __init__(self, title="Kigo App", size=(800, 600)):
        # Initialize QApplication (must be done once)
        self.qt_app = QApplication.instance()
        if self.qt_app is None:
            self.qt_app = QApplication(sys.argv)
            
        self.root = QWidget()
        self.root.setWindowTitle(title)
        self.root.resize(size[0], size[1])
        
        # Set up a basic layout
        self.layout = QVBoxLayout()
        self.root.setLayout(self.layout)

        print(f"Kigo App initialized. Version: 0.3.0")

    def add_widget(self, widget):
        """Adds a Kigo widget to the main layout."""
        # Kigo widgets expose their underlying Qt widget via .qt_widget
        if hasattr(widget, 'qt_widget'):
            self.layout.addWidget(widget.qt_widget)
        else:
            print(f"Warning: {widget.__class__.__name__} is not a recognized Kigo widget.")

    def run(self):
        """Starts the main Qt event loop."""
        self.root.show()
        # Ensure sys.exit() is used to properly close the application
        sys.exit(self.qt_app.exec())

__all__ = ['App']