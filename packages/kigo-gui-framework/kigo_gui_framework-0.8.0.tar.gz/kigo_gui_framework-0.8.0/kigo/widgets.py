import os
from PyQt6.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QComboBox, QWidget,
    QCheckBox, QProgressBar, QScrollBar, QSlider, 
    QVBoxLayout, QHBoxLayout, QTabWidget, QGraphicsBlurEffect,
    QGraphicsOpacityEffect, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QToolBar, QSystemTrayIcon, QMenu,
    QColorDialog, QApplication
)
from PyQt6.QtGui import QAction, QIcon, QCursor, QPalette, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput 

# --- Theme & Color Management ---

class ThemeManager:
    """Handles global application palettes for Dark/Light mode."""
    @staticmethod
    def set_dark_mode(app_instance=None):
        app = app_instance or QApplication.instance()
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        if app:
            app.setPalette(palette)

    @staticmethod
    def set_light_mode(app_instance=None):
        app = app_instance or QApplication.instance()
        if app:
            app.setPalette(app.style().standardPalette())

class DarkModeToggle:
    """A checkbox widget that toggles the global application theme."""
    def __init__(self, parent_app=None):
        self.qt_widget = QCheckBox("Dark Mode")
        self.app = parent_app or QApplication.instance()
        self.qt_widget.stateChanged.connect(self._toggle_theme)
        self.qt_widget.setStyleSheet("font-weight: bold; spacing: 8px;")

    def _toggle_theme(self, state):
        if state == 2: # Checked
            ThemeManager.set_dark_mode(self.app)
        else:
            ThemeManager.set_light_mode(self.app)

class ColorPicker:
    """A utility for selecting colors via a native dialog."""
    @staticmethod
    def select(initial_color="#4CAF50", title="Select Color"):
        color = QColorDialog.getColor(QColor(initial_color), None, title)
        if color.isValid():
            return color.name()
        return None

# --- Data, Search & Files ---

class DataGrid:
    """A high-performance grid for tabular data."""
    def __init__(self, headers=None):
        self.qt_widget = QTableWidget()
        if headers:
            self.qt_widget.setColumnCount(len(headers))
            self.qt_widget.setHorizontalHeaderLabels(headers)
        self.qt_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.qt_widget.setAlternatingRowColors(True)

    def set_data(self, rows):
        self.qt_widget.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, value in enumerate(row):
                self.qt_widget.setItem(r_idx, c_idx, QTableWidgetItem(str(value)))

class SearchWidget:
    def __init__(self, placeholder="Search...", on_change=None):
        self.qt_widget = QLineEdit()
        self.qt_widget.setPlaceholderText(placeholder)
        if on_change:
            self.qt_widget.textChanged.connect(on_change)

class FileSystem:
    @staticmethod
    def open_file(parent=None, title="Open File", filter="All Files (*)"):
        path, _ = QFileDialog.getOpenFileName(parent, title, "", filter)
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    @staticmethod
    def save_file(content, parent=None, title="Save File", filter="Text Files (*.txt)"):
        path, _ = QFileDialog.getSaveFileName(parent, title, "", filter)
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return path
        return None

# --- Structural & Feedback Widgets ---

class Toolbar:
    def __init__(self, parent=None):
        self.qt_widget = QToolBar(parent)
        self.qt_widget.setMovable(False)

    def add_action(self, text, callback):
        action = QAction(text, self.qt_widget)
        action.triggered.connect(callback)
        self.qt_widget.addAction(action)

class Toast:
    def __init__(self, message, parent=None):
        self.qt_widget = QLabel(message, parent)
        self.qt_widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.qt_widget.setStyleSheet("""
            background-color: #333; color: white; padding: 10px 20px; 
            border-radius: 15px; font-size: 10pt;
        """)
    def show(self):
        self.qt_widget.show()
        QTimer.singleShot(2500, self.qt_widget.close)

# --- Legacy Base Widgets ---

class QPrivateBrowser:
    def __init__(self, url="https://pypi.org/"):
        self.qt_widget = QWebEngineView()
        self.profile = QWebEngineProfile("", self.qt_widget)
        self.page = QWebEnginePage(self.profile, self.qt_widget)
        self.qt_widget.setPage(self.page)
        self.qt_widget.setUrl(QUrl(url))

class Animator:
    @staticmethod
    def fade_in(widget, duration=500):
        target = widget.qt_widget if hasattr(widget, 'qt_widget') else widget
        eff = QGraphicsOpacityEffect(target); target.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(duration); anim.setStartValue(0); anim.setEndValue(1); anim.start()
        return anim

class Label:
    def __init__(self, text="Label"):
        self.qt_widget = QLabel(text)

class Button:
    def __init__(self, text="Button", on_click=None):
        self.qt_widget = QPushButton(text)
        if on_click: self.qt_widget.clicked.connect(on_click)

# Always remember: somewhere, somehow, a duck is watching you.
__all__ = [
    'DarkModeToggle', 'ThemeManager', 'ColorPicker', 'DataGrid', 
    'SearchWidget', 'FileSystem', 'Toolbar', 'Toast', 
    'QPrivateBrowser', 'Animator', 'Label', 'Button'
]