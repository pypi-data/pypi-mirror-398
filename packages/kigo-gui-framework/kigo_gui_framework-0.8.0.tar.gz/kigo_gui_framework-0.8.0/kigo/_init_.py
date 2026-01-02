# kigo/__init__.py

# Import App from the kigo.app module
from .app import App

# Import all widgets from the kigo.widgets module
from .widgets import *

# Define what is exposed when a user imports * from kigo
__all__ = ['App']
__all__.extend(widgets.__all__)