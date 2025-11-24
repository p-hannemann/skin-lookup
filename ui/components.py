"""
Reusable UI components with consistent styling.
"""

import tkinter as tk
from tkinter import ttk
from config.styles import AppStyles


class StyledButton(tk.Button):
    """A styled button with consistent appearance and hover effects."""
    
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        """
        Create a styled button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Command to execute on click
            style: Button style - 'primary', 'success', 'danger', 'secondary'
            **kwargs: Additional button configuration options
        """
        # Set default styling based on style type
        styles = {
            'primary': {
                'bg': AppStyles.colors['primary'],
                'fg': 'white',
                'hover_bg': AppStyles.colors['primary_dark'],
                'hover_fg': 'white'
            },
            'success': {
                'bg': AppStyles.colors['success'],
                'fg': 'white',
                'hover_bg': AppStyles.colors['success_dark'],
                'hover_fg': 'white'
            },
            'danger': {
                'bg': AppStyles.colors['danger'],
                'fg': 'white',
                'hover_bg': AppStyles.colors['danger_dark'],
                'hover_fg': 'white'
            },
            'secondary': {
                'bg': AppStyles.colors['card'],
                'fg': AppStyles.colors['primary'],
                'hover_bg': AppStyles.colors['primary'],
                'hover_fg': 'white'
            }
        }
        
        style_config = styles.get(style, styles['primary'])
        
        # Default button configuration
        borderwidth_val = 1 if style == 'secondary' else 0
        relief_val = tk.SOLID if style == 'secondary' else tk.FLAT
        
        config = {
            'font': AppStyles.fonts['button'],
            'bg': style_config['bg'],
            'fg': style_config['fg'],
            'relief': relief_val,
            'borderwidth': borderwidth_val,
            'padx': 15,
            'pady': 6,
            'cursor': 'hand2'
        }
        
        # Merge with user-provided kwargs
        config.update(kwargs)
        
        super().__init__(parent, text=text, command=command, **config)
        
        # Add hover effect
        AppStyles.add_button_hover(self, style_config['hover_bg'], style_config['hover_fg'])


class StyledEntry(tk.Entry):
    """A styled entry field with consistent appearance."""
    
    def __init__(self, parent, **kwargs):
        """
        Create a styled entry field.
        
        Args:
            parent: Parent widget
            **kwargs: Additional entry configuration options
        """
        config = {
            'font': AppStyles.fonts['body'],
            'relief': tk.SOLID,
            'borderwidth': 1
        }
        
        config.update(kwargs)
        super().__init__(parent, **config)


class StyledLabel(tk.Label):
    """A styled label with consistent appearance."""
    
    def __init__(self, parent, text="", style="body", **kwargs):
        """
        Create a styled label.
        
        Args:
            parent: Parent widget
            text: Label text
            style: Font style - 'heading', 'subheading', 'body', 'body_small', 'body_tiny'
            **kwargs: Additional label configuration options
        """
        config = {
            'font': AppStyles.fonts.get(style, AppStyles.fonts['body']),
            'bg': kwargs.get('bg', AppStyles.colors['card']),
            'fg': AppStyles.colors['text']
        }
        
        config.update(kwargs)
        super().__init__(parent, text=text, **config)


class CardFrame(tk.Frame):
    """A card-style frame with consistent styling."""
    
    def __init__(self, parent, **kwargs):
        """
        Create a card frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional frame configuration options
        """
        config = {
            'bg': AppStyles.colors['card'],
            'relief': tk.FLAT,
            'borderwidth': 0
        }
        
        config.update(kwargs)
        super().__init__(parent, **config)


class StyledCombobox(ttk.Combobox):
    """A styled combobox with consistent appearance."""
    
    def __init__(self, parent, **kwargs):
        """
        Create a styled combobox.
        
        Args:
            parent: Parent widget
            **kwargs: Additional combobox configuration options
        """
        config = {
            'font': AppStyles.fonts['body_small'],
            'state': 'readonly'
        }
        
        config.update(kwargs)
        super().__init__(parent, **config)
