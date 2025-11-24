"""
Browser tab - Simple skin image browser.
"""

import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from ui.tabs.base_tab import BaseTab
from ui.image_viewer import ImageViewerWindow


class BrowserTab(BaseTab):
    """Tab for browsing skin images."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_ui()
    
    def create_ui(self):
        """Create the browser tab UI."""
        # Instructions banner
        instructions_frame = tk.Frame(self.frame, bg="#E8F5E9", padx=15, pady=10, relief=tk.FLAT)
        instructions_frame.pack(fill=tk.X, padx=15, pady=(15, 0))
        
        tk.Label(instructions_frame, 
                text="🖼️ Browse Minecraft skins", 
                font=("Segoe UI", 10, "bold"), 
                bg="#E8F5E9",
                fg=self.colors['success']).pack(anchor=tk.W)
        tk.Label(instructions_frame, 
                text="Select a directory to browse through skin images without copying or matching", 
                font=("Segoe UI", 9), 
                bg="#E8F5E9",
                fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(2, 0))
        
        # Main content card
        content_card = tk.Frame(self.frame, bg=self.colors['card'], relief=tk.FLAT)
        content_card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Directory selection
        frame_dir = tk.Frame(content_card, bg=self.colors['card'], padx=20, pady=15)
        frame_dir.pack(fill=tk.X)
        
        tk.Label(frame_dir, 
                text="Browse Directory", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W)
        
        dir_frame = tk.Frame(frame_dir, bg=self.colors['card'])
        dir_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.browser_dir_path = tk.StringVar()
        # Set default to Prism Launcher skins folder if it exists
        prism_skins_path = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "PrismLauncher" / "assets" / "skins"
        if prism_skins_path.exists():
            self.browser_dir_path.set(str(prism_skins_path))
        
        entry = tk.Entry(dir_frame, 
                        textvariable=self.browser_dir_path, 
                        font=("Segoe UI", 10),
                        relief=tk.SOLID,
                        borderwidth=1)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        
        browse_dir_btn = tk.Button(dir_frame, 
                                   text="Browse...", 
                                   command=self.browse_browser_directory,
                                   font=("Segoe UI", 9),
                                   bg=self.colors['card'],
                                   fg=self.colors['primary'],
                                   relief=tk.SOLID,
                                   borderwidth=1,
                                   padx=15,
                                   pady=6,
                                   cursor="hand2")
        browse_dir_btn.pack(side=tk.RIGHT)
        self.add_button_hover(browse_dir_btn, self.colors['primary'], '#ffffff')
        
        # Buttons
        btn_frame = tk.Frame(content_card, bg=self.colors['card'], padx=20)
        btn_frame.pack(fill=tk.X, pady=(10, 20))
        
        open_browser_btn = tk.Button(btn_frame, 
                                     text="🖼️ Open Skin Browser", 
                                     command=self.open_skin_browser,
                                     font=("Segoe UI", 11, "bold"),
                                     bg=self.colors['success'],
                                     fg="white",
                                     relief=tk.FLAT,
                                     padx=20,
                                     pady=12,
                                     cursor="hand2")
        open_browser_btn.pack(side=tk.LEFT, padx=4)
        self.add_button_hover(open_browser_btn, self.colors['success_dark'], 'white', flat=True)
        
        # Info text
        info_frame = tk.Frame(content_card, bg=self.colors['card'], padx=20)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        info_text = (
            "Browse through skin images with keyboard navigation:\n\n"
            "• ← → Arrow keys to navigate between images\n"
            "• Explorer: Open file location in Windows Explorer\n"
            "• Viewer: Open in Windows default image viewer\n"
            "• Paint: Open in Microsoft Paint for editing"
        )
        
        tk.Label(info_frame, 
                text=info_text, 
                font=("Segoe UI", 9),
                bg=self.colors['card'],
                fg=self.colors['text_secondary'],
                justify=tk.LEFT).pack(anchor=tk.W)
    
    def browse_browser_directory(self):
        """Browse for a directory to view skins."""
        prism_skins_path = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "PrismLauncher" / "assets" / "skins"
        initial_dir = str(prism_skins_path) if prism_skins_path.exists() else os.getcwd()
        
        folder = filedialog.askdirectory(title="Select Directory to Browse", initialdir=initial_dir)
        if folder:
            self.browser_dir_path.set(folder)
    
    def open_skin_browser(self):
        """Open the image viewer for the selected directory."""
        from tkinter import messagebox
        
        browse_dir = self.browser_dir_path.get()
        
        if not browse_dir:
            messagebox.showerror("Error", "Please select a directory first")
            return
        
        if not os.path.exists(browse_dir):
            messagebox.showerror("Error", "Directory does not exist")
            return
        
        ImageViewerWindow(self.root, browse_dir)
