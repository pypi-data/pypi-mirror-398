"""
NVLib.component
===============
Optimized for lazy loading to prevent unnecessary dependency crashes.
"""

__all__ = ["Audio", "Authentication", "Database", "GUI", "VisualRec"]

def __getattr__(name):
    if name == "Audio":
        from . import Audio
        return Audio
    if name == "Authentication":
        from . import Authentication
        return Authentication
    if name == "Database":
        from . import Database
        return Database
    if name == "GUI":
        from . import GUI
        return GUI
    if name == "VisualRec":
        from . import VisualRec
        return VisualRec
    raise AttributeError(f"module {__name__} has no attribute {name}")