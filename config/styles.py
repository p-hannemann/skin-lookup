"""
Shared styling configuration for the application.
Provides consistent colors, fonts, and styling functions.
"""

import tkinter as tk
from tkinter import ttk


class AppStyles:
    """Central configuration for application colors and styles."""
    
    # Color scheme
    colors = {
        'primary': '#2196F3',
        'primary_dark': '#1976D2',
        'success': '#4CAF50',
        'success_dark': '#388E3C',
        'danger': '#f44336',
        'danger_dark': '#D32F2F',
        'bg': '#f5f5f5',
        'card': '#ffffff',
        'text': '#212121',
        'text_secondary': '#757575',
        'border': '#e0e0e0'
    }
    
    # Font configurations
    fonts = {
        'heading': ('Segoe UI', 11, 'bold'),
        'subheading': ('Segoe UI', 10, 'bold'),
        'body': ('Segoe UI', 10),
        'body_small': ('Segoe UI', 9),
        'body_tiny': ('Segoe UI', 8),
        'button': ('Segoe UI', 9),
        'button_large': ('Segoe UI', 11, 'bold')
    }
    
    @staticmethod
    def configure_ttk_styles():
        """Configure ttk widget styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Notebook (tabs) styling
        style.configure('TNotebook', 
                       background=AppStyles.colors['bg'], 
                       borderwidth=0, 
                       tabmargins=[0, 0, 0, 0])
        style.configure('TNotebook.Tab', 
                       padding=[20, 10], 
                       font=AppStyles.fonts['body'],
                       background=AppStyles.colors['card'],
                       borderwidth=0,
                       width=15)
        style.map('TNotebook.Tab', 
                 background=[('selected', AppStyles.colors['card']), 
                           ('!selected', AppStyles.colors['card'])],
                 foreground=[('selected', AppStyles.colors['primary']), 
                           ('!selected', AppStyles.colors['text'])],
                 borderwidth=[('selected', 0), ('!selected', 0)],
                 padding=[('selected', [20, 10]), ('!selected', [20, 10])])
        
        # Combobox styling
        style.configure('TCombobox',
                       fieldbackground=AppStyles.colors['card'],
                       background=AppStyles.colors['card'],
                       foreground=AppStyles.colors['text'],
                       borderwidth=1,
                       relief='solid')
    
    @staticmethod
    def add_button_hover(button, hover_bg, hover_fg=None):
        """
        Add hover effect to a button.
        
        Args:
            button: The tkinter button widget
            hover_bg: Background color on hover
            hover_fg: Foreground color on hover (optional)
        """
        original_bg = button.cget('bg')
        original_fg = button.cget('fg')
        
        def on_enter(e):
            if button['state'] != 'disabled':
                button['bg'] = hover_bg
                if hover_fg:
                    button['fg'] = hover_fg
        
        def on_leave(e):
            if button['state'] != 'disabled':
                button['bg'] = original_bg
                button['fg'] = original_fg
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
