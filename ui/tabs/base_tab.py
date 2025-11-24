"""
Base class for GUI tabs.
"""

import tkinter as tk


class BaseTab:
    """Base class for all GUI tabs."""
    
    def __init__(self, parent, app):
        """
        Initialize the tab.
        
        Args:
            parent: Parent widget (notebook)
            app: Reference to main SkinCopierGUI instance
        """
        self.parent = parent
        self.app = app
        self.root = app.root
        self.colors = app.colors
        self.verbose = app.verbose
        
        # Create the tab frame
        self.frame = tk.Frame(parent, bg=self.colors['bg'])
        
    def debug_log(self, message):
        """Log debug messages if verbose mode is enabled."""
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def add_button_hover(self, button, hover_bg, hover_fg=None, flat=False):
        """Add hover effect to a button."""
        from config.styles import AppStyles
        AppStyles.add_button_hover(button, hover_bg, hover_fg)
