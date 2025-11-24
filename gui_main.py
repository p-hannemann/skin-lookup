"""
Main GUI application for Skin Lookup Tool with integrated skin matching.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
from pathlib import Path
import subprocess
import urllib.request
import io
import numpy as np
from PIL import Image, ImageTk

# Global debug flag
DEBUG = False

from utils.file_utils import copy_and_rename_to_png
from utils.skin_matcher import find_matching_skins, copy_skin_files
from utils.wiki_parser import parse_wiki_for_image, download_image_from_url
from ui.image_viewer import ImageViewerWindow
from config.styles import AppStyles
from app_info import __app_name__, __version__
from ui.tabs import ConverterTab, BrowserTab


class SkinCopierGUI:
    def __init__(self, root, verbose=False):
        self.root = root
        self.verbose = verbose
        self.root.title(f"{__app_name__} v{__version__}")
        self.root.geometry("850x900")
        self.root.resizable(True, True)
        self.is_processing = False
        self.should_cancel = False
        self.current_output_dir = None
        self.last_output_dir = None
        self.preview_window = None
        self.example_image_url = "https://www.minecraftskins.com/uploads/preview-skins/2022/03/22/minos-inquisitor-20083594.png"
        self.temp_downloaded_image = None
        
        if self.verbose:
            print("[DEBUG] Initializing SkinCopierGUI...")
            print(f"[DEBUG] App: {__app_name__} v{__version__}")
        
        # Use shared color scheme
        self.colors = AppStyles.colors
        
        # Configure root background
        self.root.configure(bg=self.colors['bg'])
        
        # Configure ttk styles using shared configuration
        AppStyles.configure_ttk_styles()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_matcher_tab()
        self.create_copier_tab()
        
        # Create browser tab using new modular system
        self.browser_tab = BrowserTab(self.notebook, self)
        self.notebook.add(self.browser_tab.frame, text="🔍 Skin Browser")
        
        # Create converter tab using new modular system
        self.converter_tab = ConverterTab(self.notebook, self)
        self.notebook.add(self.converter_tab.frame, text="🔄 Converter")
        
        # Progress bar at the very bottom
        self.progress_frame = tk.Frame(root, bg=self.colors['bg'])
        self.progress_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, expand=True)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 8),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        self.progress_label.pack(pady=(2, 0))
        
        # Initially hide the progress bar
        self.progress_frame.pack_forget()
        
        # Footer with credits
        footer_frame = tk.Frame(root, padx=15, pady=10, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        credits_label = tk.Label(footer_frame, 
                                text="☕ Made by SoulReturns", 
                                font=("Segoe UI", 9),
                                fg=self.colors['text_secondary'],
                                bg=self.colors['bg'])
        credits_label.pack(side=tk.LEFT)
        
        discord_label = tk.Label(footer_frame, 
                                text="Discord: soulreturns", 
                                font=("Segoe UI", 9),
                                fg="#5865F2",
                                bg=self.colors['bg'],
                                cursor="hand2")
        discord_label.pack(side=tk.RIGHT)
        discord_label.bind("<Button-1>", lambda e: self.open_discord())
        discord_label.bind("<Enter>", lambda e: discord_label.config(font=("Segoe UI", 9, "underline")))
        discord_label.bind("<Leave>", lambda e: discord_label.config(font=("Segoe UI", 9)))
    
    def debug_log(self, message):
        """Log debug messages if verbose mode is enabled."""
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def create_matcher_tab(self):
        """Create the skin matcher tab."""
        self.debug_log("Creating matcher tab...")
        matcher_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(matcher_frame, text="🔍 Skin Matcher")
        
        # Instructions banner
        instructions_frame = tk.Frame(matcher_frame, bg="#E3F2FD", relief=tk.FLAT, padx=15, pady=12)
        instructions_frame.pack(fill=tk.X, padx=15, pady=(15, 0))
        
        tk.Label(instructions_frame, 
                text="💡 Find skins in Prism Launcher's cache", 
                font=("Segoe UI", 10, "bold"), 
                bg="#E3F2FD",
                fg=self.colors['primary']).pack(anchor=tk.W)
        tk.Label(instructions_frame, 
                text="Select your rendered skin image, then browse to: AppData\\Roaming\\PrismLauncher\\assets\\skins", 
                font=("Segoe UI", 9), 
                bg="#E3F2FD",
                fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(2, 0))
        
        # Main content card
        content_card = tk.Frame(matcher_frame, bg=self.colors['card'], relief=tk.FLAT)
        content_card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Input image selection
        frame_input = tk.Frame(content_card, bg=self.colors['card'], padx=20, pady=15)
        frame_input.pack(fill=tk.X)
        
        tk.Label(frame_input, 
                text="Input Image", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W)
        
        # Input method selection (radio buttons)
        method_frame = tk.Frame(frame_input, bg=self.colors['card'])
        method_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.input_method = tk.StringVar(value="file")
        
        tk.Radiobutton(method_frame,
                      text="Local File",
                      variable=self.input_method,
                      value="file",
                      bg=self.colors['card'],
                      font=("Segoe UI", 9),
                      command=self.on_input_method_change).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(method_frame,
                      text="Direct URL",
                      variable=self.input_method,
                      value="url",
                      bg=self.colors['card'],
                      font=("Segoe UI", 9),
                      command=self.on_input_method_change).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(method_frame,
                      text="Hypixel Wiki",
                      variable=self.input_method,
                      value="wiki",
                      bg=self.colors['card'],
                      font=("Segoe UI", 9),
                      command=self.on_input_method_change).pack(side=tk.LEFT)
        
        img_frame = tk.Frame(frame_input, bg=self.colors['card'])
        img_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.input_image_path = tk.StringVar()
        self.input_image_path.trace_add('write', lambda *args: self.on_input_path_changed())
        self.input_image_entry = tk.Entry(img_frame, 
                        textvariable=self.input_image_path, 
                        font=("Segoe UI", 10),
                        relief=tk.SOLID,
                        borderwidth=1)
        self.input_image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        
        self.browse_img_btn = tk.Button(img_frame, 
                                   text="Browse...", 
                                   command=self.browse_input_image,
                                   font=("Segoe UI", 9),
                                   bg=self.colors['card'],
                                   fg=self.colors['primary'],
                                   relief=tk.SOLID,
                                   borderwidth=1,
                                   padx=15,
                                   pady=6,
                                   cursor="hand2")
        self.browse_img_btn.pack(side=tk.RIGHT)
        self._add_button_hover(self.browse_img_btn, self.colors['primary'], '#ffffff')
        
        self.preview_input_btn = tk.Button(img_frame,
                                           text="🖼️ Preview",
                                           command=self.show_input_preview_window,
                                           font=("Segoe UI", 9),
                                           bg=self.colors['card'],
                                           fg=self.colors['primary'],
                                           relief=tk.SOLID,
                                           borderwidth=1,
                                           padx=15,
                                           pady=6,
                                           cursor="hand2",
                                           state=tk.DISABLED)
        self.preview_input_btn.pack(side=tk.RIGHT, padx=(0, 8))
        self._add_button_hover(self.preview_input_btn, self.colors['primary'], '#ffffff')
        
        # Store preview data
        self.input_preview_image = None
        
        example_img_btn = tk.Button(img_frame, 
                                    text="Example", 
                                    command=self.load_example_image,
                                    font=("Segoe UI", 9),
                                    bg=self.colors['card'],
                                    fg=self.colors['success'],
                                    relief=tk.SOLID,
                                    borderwidth=1,
                                    padx=15,
                                    pady=6,
                                    cursor="hand2")
        example_img_btn.pack(side=tk.RIGHT, padx=(0, 8))
        self._add_button_hover(example_img_btn, self.colors['success'], '#ffffff')
        example_img_btn.bind('<Enter>', self.show_example_preview)
        example_img_btn.bind('<Leave>', self.hide_example_preview)
        
        # Search directory selection
        tk.Label(frame_input, 
                text="Search Directory", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W, pady=(15, 0))
        
        dir_frame = tk.Frame(frame_input, bg=self.colors['card'])
        dir_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.search_dir_path = tk.StringVar()
        entry2 = tk.Entry(dir_frame, 
                         textvariable=self.search_dir_path, 
                         font=("Segoe UI", 10),
                         relief=tk.SOLID,
                         borderwidth=1)
        entry2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        
        browse_dir_btn = tk.Button(dir_frame, 
                                   text="Browse...", 
                                   command=self.browse_search_directory,
                                   font=("Segoe UI", 9),
                                   bg=self.colors['card'],
                                   fg=self.colors['primary'],
                                   relief=tk.SOLID,
                                   borderwidth=1,
                                   padx=15,
                                   pady=6,
                                   cursor="hand2")
        browse_dir_btn.pack(side=tk.RIGHT)
        self._add_button_hover(browse_dir_btn, self.colors['primary'], '#ffffff')
        
        # Number of matches
        match_frame = tk.Frame(frame_input, bg=self.colors['card'])
        match_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Label(match_frame, 
                text="Top matches:", 
                font=("Segoe UI", 9),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        self.top_n_matches = tk.IntVar(value=5)
        spinner = tk.Spinbox(match_frame, 
                            from_=1, 
                            to=20, 
                            textvariable=self.top_n_matches, 
                            width=6, 
                            font=("Segoe UI", 10),
                            relief=tk.SOLID,
                            borderwidth=1)
        spinner.pack(side=tk.LEFT, padx=8)
        
        # Algorithm selection
        algo_frame = tk.Frame(frame_input, bg=self.colors['card'])
        algo_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Label(algo_frame, 
                text="Algorithm:", 
                font=("Segoe UI", 9),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.algorithm_choice = tk.StringVar(value="Balanced (Default)")
        algorithm_dropdown = ttk.Combobox(algo_frame,
                                         textvariable=self.algorithm_choice,
                                         state="readonly",
                                         width=25,
                                         font=("Segoe UI", 9))
        algorithm_dropdown['values'] = (
            "Balanced (Default)",
            "Render to Skin (Convert+Match)",
            "Render Match (3D→2D)",
            "Skin-Optimized",
            "AI Perceptual (ResNet18)",
            "AI Mobile (ResNet50)",
            "Deep Features",
            "Color Distribution",
            "Fast Match"
        )
        algorithm_dropdown.current(0)
        algorithm_dropdown.pack(side=tk.LEFT, padx=8)
        algorithm_dropdown.bind("<<ComboboxSelected>>", self.on_algorithm_change)
        
        # Algorithm info button
        info_btn = tk.Label(algo_frame,
                           text="ℹ️",
                           font=("Segoe UI", 12),
                           bg=self.colors['card'],
                           fg=self.colors['primary'],
                           cursor="hand2")
        info_btn.pack(side=tk.LEFT, padx=5)
        info_btn.bind("<Button-1>", self.show_algorithm_info)
        
        # Preview Converted Image button (hidden by default, shown only for render_to_skin)
        self.preview_btn = tk.Button(algo_frame,
                                     text="👁️ Preview Conversion",
                                     command=self.preview_converted_image,
                                     font=("Segoe UI", 9),
                                     bg=self.colors['primary'],
                                     fg="white",
                                     relief=tk.FLAT,
                                     padx=12,
                                     pady=4,
                                     cursor="hand2",
                                     state=tk.DISABLED)
        # Start packed since render_to_skin is default
        self.preview_btn.pack(side=tk.LEFT, padx=8)
        self._add_button_hover(self.preview_btn, self.colors['primary_dark'], 'white', flat=True)
        
        # AI Test button (hidden by default)
        self.ai_test_btn = tk.Button(algo_frame,
                                      text="🧪 Test AI",
                                      command=self.test_ai_availability,
                                      font=("Segoe UI", 9),
                                      bg=self.colors['primary'],
                                      fg="white",
                                      relief=tk.FLAT,
                                      padx=12,
                                      pady=4,
                                      cursor="hand2")
        # Don't pack yet - will show/hide based on selection
        self._add_button_hover(self.ai_test_btn, self.colors['primary_dark'], 'white', flat=True)
        

        
        # Buttons frame
        btn_frame = tk.Frame(content_card, bg=self.colors['card'], pady=15)
        btn_frame.pack(fill=tk.X, padx=20)
        
        self.match_btn = tk.Button(btn_frame, 
                                   text="🔍 Find Matching Skins", 
                                   command=self.find_matches,
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.colors['success'],
                                   fg="white",
                                   relief=tk.FLAT,
                                   padx=25, 
                                   pady=12,
                                   cursor="hand2")
        self.match_btn.pack(side=tk.LEFT, padx=(0, 8))
        self._add_button_hover(self.match_btn, self.colors['success_dark'], 'white', flat=True)
        
        self.match_cancel_btn = tk.Button(btn_frame, 
                                         text="Cancel", 
                                         command=self.cancel_matching,
                                         font=("Segoe UI", 10),
                                         bg=self.colors['danger'],
                                         fg="white",
                                         relief=tk.FLAT,
                                         padx=20, 
                                         pady=12,
                                         cursor="hand2",
                                         state=tk.DISABLED)
        self.match_cancel_btn.pack(side=tk.LEFT, padx=4)
        self._add_button_hover(self.match_cancel_btn, self.colors['danger_dark'], 'white', flat=True)
        
        self.view_matches_btn = tk.Button(btn_frame, 
                                         text="👁️ View Results", 
                                         command=self.view_match_results,
                                         font=("Segoe UI", 10),
                                         bg=self.colors['primary'],
                                         fg="white",
                                         relief=tk.FLAT,
                                         padx=20, 
                                         pady=12,
                                         cursor="hand2",
                                         state=tk.DISABLED)
        self.view_matches_btn.pack(side=tk.LEFT, padx=4)
        self._add_button_hover(self.view_matches_btn, self.colors['primary_dark'], 'white', flat=True)
        
        # Log area
        log_frame = tk.Frame(content_card, bg=self.colors['card'], padx=20)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        tk.Label(log_frame, 
                text="Activity Log", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W, pady=5)
        
        self.matcher_log_text = scrolledtext.ScrolledText(log_frame, 
                                                          height=8, 
                                                          font=("Consolas", 9),
                                                          relief=tk.SOLID,
                                                          borderwidth=1,
                                                          state=tk.DISABLED)
        self.matcher_log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_copier_tab(self):
        """Create the file copier tab."""
        copier_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(copier_frame, text="📁 File Copier")
        
        # Instructions banner
        instructions_frame = tk.Frame(copier_frame, bg="#FFF3E0", relief=tk.FLAT, padx=15, pady=12)
        instructions_frame.pack(fill=tk.X, padx=15, pady=(15, 0))
        
        tk.Label(instructions_frame, 
                text="💡 Batch copy files with .png extension", 
                font=("Segoe UI", 10, "bold"), 
                bg="#FFF3E0",
                fg="#F57C00").pack(anchor=tk.W)
        tk.Label(instructions_frame, 
                text="Select a folder and files will be copied to [folder]_png with .png extension automatically added", 
                font=("Segoe UI", 9), 
                bg="#FFF3E0",
                fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(2, 0))
        
        # Main content card
        content_card = tk.Frame(copier_frame, bg=self.colors['card'], relief=tk.FLAT)
        content_card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Input folder selection
        frame_input = tk.Frame(content_card, bg=self.colors['card'], padx=20, pady=15)
        frame_input.pack(fill=tk.X)
        
        tk.Label(frame_input, 
                text="Input Folder", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W)
        
        folder_frame = tk.Frame(frame_input, bg=self.colors['card'])
        folder_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.folder_path = tk.StringVar()
        entry = tk.Entry(folder_frame, 
                        textvariable=self.folder_path, 
                        font=("Segoe UI", 10),
                        relief=tk.SOLID,
                        borderwidth=1)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        
        browse_btn = tk.Button(folder_frame, 
                              text="Browse...", 
                              command=self.browse_folder,
                              font=("Segoe UI", 9),
                              bg=self.colors['card'],
                              fg=self.colors['primary'],
                              relief=tk.SOLID,
                              borderwidth=1,
                              padx=15,
                              pady=6,
                              cursor="hand2")
        browse_btn.pack(side=tk.RIGHT)
        self._add_button_hover(browse_btn, self.colors['primary'], '#ffffff')
        
        # Info label
        info_label = tk.Label(frame_input, 
                             text="→ Output will be created as: [input_folder]_png", 
                             fg=self.colors['text_secondary'], 
                             bg=self.colors['card'],
                             font=("Segoe UI", 9))
        info_label.pack(anchor=tk.W, pady=(8, 0))
        
        # Merge files toggle
        self.merge_files = tk.BooleanVar(value=False)
        merge_check = tk.Checkbutton(frame_input, 
                                     text="Merge all files into single folder (no subdirectories)",
                                     variable=self.merge_files,
                                     bg=self.colors['card'],
                                     font=("Segoe UI", 9))
        merge_check.pack(anchor=tk.W, pady=(12, 0))
        
        # Buttons frame
        btn_frame = tk.Frame(content_card, bg=self.colors['card'], pady=15)
        btn_frame.pack(fill=tk.X, padx=20)
        
        self.process_btn = tk.Button(btn_frame, 
                                     text="📦 Copy and Add .png Extension", 
                                     command=self.process_folder, 
                                     font=("Segoe UI", 11, "bold"),
                                     bg=self.colors['success'],
                                     fg="white",
                                     relief=tk.FLAT,
                                     padx=25,
                                     pady=12,
                                     cursor="hand2")
        self.process_btn.pack(side=tk.LEFT, padx=(0, 8))
        self._add_button_hover(self.process_btn, self.colors['success_dark'], 'white', flat=True)
        
        self.cancel_btn = tk.Button(btn_frame, 
                                    text="Cancel", 
                                    command=self.cancel_process, 
                                    font=("Segoe UI", 10),
                                    bg=self.colors['danger'],
                                    fg="white",
                                    relief=tk.FLAT,
                                    padx=20,
                                    pady=12,
                                    cursor="hand2",
                                    state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=4)
        self._add_button_hover(self.cancel_btn, self.colors['danger_dark'], 'white', flat=True)
        
        self.viewer_btn = tk.Button(btn_frame, 
                                    text="👁️ View Images", 
                                    command=self.open_image_viewer, 
                                    font=("Segoe UI", 10),
                                    bg=self.colors['primary'],
                                    fg="white",
                                    relief=tk.FLAT,
                                    padx=20,
                                    pady=12,
                                    cursor="hand2")
        self.viewer_btn.pack(side=tk.LEFT, padx=4)
        self._add_button_hover(self.viewer_btn, self.colors['primary_dark'], 'white', flat=True)
        
        # Check for existing output directory on startup
        self.check_for_existing_output()
        self.update_viewer_button_state()
        
        # Log area
        log_frame = tk.Frame(content_card, bg=self.colors['card'], padx=20)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        tk.Label(log_frame, 
                text="Activity Log", 
                font=("Segoe UI", 10, "bold"),
                bg=self.colors['card'],
                fg=self.colors['text']).pack(anchor=tk.W, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                  height=8, 
                                                  font=("Consolas", 9),
                                                  relief=tk.SOLID,
                                                  borderwidth=1,
                                                  state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _add_button_hover(self, button, hover_bg, hover_fg=None, flat=False):
        """Add hover effect to a button. Delegates to AppStyles."""
        AppStyles.add_button_hover(button, hover_bg, hover_fg)
    
    def browse_input_image(self):
        self.debug_log("Opening file browser for input image...")
        initial_dir = os.getcwd()
        file_path = filedialog.askopenfilename(
            title="Select Input Image",
            initialdir=initial_dir,
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            self.debug_log(f"Selected input image: {file_path}")
            self.input_image_path.set(file_path)
        else:
            self.debug_log("File browser cancelled")
    
    def browse_search_directory(self):
        # Try to use Prism Launcher assets folder if it exists
        prism_skins_path = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "PrismLauncher" / "assets"
        if prism_skins_path.exists():
            initial_dir = str(prism_skins_path)
        else:
            initial_dir = os.getcwd()
        
        folder = filedialog.askdirectory(title="Select Search Directory", initialdir=initial_dir)
        if folder:
            self.search_dir_path.set(folder)
    
    def load_example_image(self):
        """Download and save the example image to input folder."""
        def download_task():
            try:
                self.matcher_log("Downloading example image...")
                
                # Create input folder if it doesn't exist
                input_folder = Path("input")
                input_folder.mkdir(exist_ok=True)
                
                # Download the image
                with urllib.request.urlopen(self.example_image_url) as response:
                    image_data = response.read()
                
                # Save to input folder
                output_path = input_folder / "example_minos_inquisitor.png"
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                # Set the path in the input field
                self.input_image_path.set(str(output_path.absolute()))
                self.matcher_log(f"Example image saved to: {output_path.absolute()}")
                messagebox.showinfo("Success", f"Example image downloaded to:\n{output_path.absolute()}")
                
            except Exception as e:
                self.matcher_log(f"Error downloading example image: {str(e)}")
                messagebox.showerror("Error", f"Failed to download example image:\n{str(e)}")
        
        thread = threading.Thread(target=download_task, daemon=True)
        thread.start()
    
    def show_example_preview(self, event):
        """Show preview of example image on hover."""
        try:
            # Create preview window
            self.preview_window = tk.Toplevel(self.root)
            self.preview_window.overrideredirect(True)  # Remove window decorations
            self.preview_window.attributes('-topmost', True)
            
            # Position near the button
            x = event.widget.winfo_rootx() + event.widget.winfo_width() + 10
            y = event.widget.winfo_rooty()
            self.preview_window.geometry(f"+{x}+{y}")
            
            # Download and display preview
            with urllib.request.urlopen(self.example_image_url) as response:
                image_data = response.read()
            
            img = Image.open(io.BytesIO(image_data))
            # Resize for preview (max 300x300)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(self.preview_window, image=photo, bg='white', relief=tk.SOLID, borderwidth=2)
            label.image = photo  # Keep a reference
            label.pack()
            
        except Exception as e:
            # If preview fails, just skip it
            if self.preview_window:
                self.preview_window.destroy()
                self.preview_window = None
    
    def hide_example_preview(self, event):
        """Hide the preview window."""
        if self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None
    
    def matcher_log(self, message):
        self.matcher_log_text.config(state=tk.NORMAL)
        self.matcher_log_text.insert(tk.END, message + "\n")
        self.matcher_log_text.see(tk.END)
        self.matcher_log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def download_image_from_url(self, url):
        """Download image from URL and save temporarily."""
        try:
            self.matcher_log(f"Downloading image from URL...")
            
            # Use the utility function with debug callback
            img = download_image_from_url(url, debug_callback=self.debug_log)
            
            if img:
                # Create temp folder if it doesn't exist
                temp_folder = Path("temp")
                temp_folder.mkdir(exist_ok=True)
                
                # Save to temp folder
                temp_path = temp_folder / "temp_input_image.png"
                img.save(temp_path)
                self.debug_log(f"Image saved to: {temp_path.absolute()}")
                
                self.temp_downloaded_image = str(temp_path.absolute())
                self.matcher_log(f"Image downloaded successfully")
                return str(temp_path.absolute())
            else:
                return None
        except Exception as e:
            self.matcher_log(f"Error downloading image: {str(e)}")
            messagebox.showerror("Error", f"Failed to download image:\n{str(e)}")
            return None
    
    def parse_hypixel_wiki_image(self, wiki_url):
        """Parse Hypixel wiki page to find the sprite head icon image."""
        try:
            self.matcher_log(f"Parsing Hypixel Wiki page...")
            
            # Use the utility function with debug callback
            img = parse_wiki_for_image(wiki_url, debug_callback=self.debug_log)
            
            if img:
                # Save to temporary file
                input_folder = Path("input")
                input_folder.mkdir(exist_ok=True)
                temp_path = input_folder / "temp_wiki_image.png"
                img.save(temp_path)
                self.matcher_log(f"Image downloaded and saved to: {temp_path}")
                return str(temp_path.absolute())
            else:
                return None
            
        except Exception as e:
            self.matcher_log(f"Error parsing wiki page: {str(e)}")
            messagebox.showerror("Error", f"Failed to parse Hypixel wiki page:\n{str(e)}\n\nTip: You can try using Direct URL mode with the image URL instead.")
            return None
    
    def find_matches(self):
        self.debug_log("=== Find Matches Started ===")
        input_image = self.input_image_path.get()
        search_dir = self.search_dir_path.get()
        method = self.input_method.get()
        self.debug_log(f"Input method: {method}")
        self.debug_log(f"Input image/URL: {input_image}")
        self.debug_log(f"Search directory: {search_dir}")
        
        # Check for placeholder text
        if self.input_image_entry.cget('fg') == 'gray':
            input_image = ""
        
        if not input_image:
            self.debug_log("No input provided")
            messagebox.showwarning("No Image Selected", "Please provide an input image path or URL.")
            return
        
        if not search_dir:
            messagebox.showwarning("No Directory Selected", "Please select a search directory.")
            return
        
        # Handle different input methods
        actual_image_path = None
        
        if method == "file":
            self.debug_log("Processing as local file...")
            if not os.path.exists(input_image):
                self.debug_log(f"File not found: {input_image}")
                messagebox.showerror("Error", f"Input image does not exist: {input_image}")
                return
            actual_image_path = input_image
            self.debug_log(f"Using local file: {actual_image_path}")
        elif method == "url":
            self.debug_log("Processing as direct URL...")
            # Download image from URL
            actual_image_path = self.download_image_from_url(input_image)
            if not actual_image_path:
                self.debug_log("URL download failed")
                return
        elif method == "wiki":
            self.debug_log("Processing as Hypixel Wiki URL...")
            # Parse Hypixel wiki page
            actual_image_path = self.parse_hypixel_wiki_image(input_image)
            if not actual_image_path:
                self.debug_log("Wiki parsing failed")
                return
        
        if not os.path.exists(search_dir):
            messagebox.showerror("Error", f"Search directory does not exist: {search_dir}")
            return
        
        # Warn about AI algorithms on large datasets
        algo_choice = self.algorithm_choice.get()
        if "AI" in algo_choice:
            # Quick file count estimate
            from pathlib import Path
            file_count = sum(1 for _ in Path(search_dir).rglob('*') if _.is_file())
            if file_count > 10000:
                estimated_time = (file_count / 50) / 60  # ~50 files/sec on GPU, convert to minutes
                response = messagebox.askyesno(
                    "Large Dataset Warning",
                    f"Found ~{file_count:,} files.\n\n"
                    f"AI algorithms are SLOW on large datasets!\n"
                    f"Estimated time: {int(estimated_time)} minutes\n\n"
                    f"💡 Recommendation:\n"
                    f"• Use 'Fast Match' or 'Color Distribution' first\n"
                    f"• Or reduce your search directory size\n\n"
                    f"Continue with AI algorithm anyway?",
                    icon='warning'
                )
                if not response:
                    return
        
        # Clear log
        self.matcher_log_text.config(state=tk.NORMAL)
        self.matcher_log_text.delete(1.0, tk.END)
        self.matcher_log_text.config(state=tk.DISABLED)
        
        # Reset cancel flag
        self.should_cancel = False
        
        # Update button states
        self.match_btn.config(state=tk.DISABLED)
        self.match_cancel_btn.config(state=tk.NORMAL)
        self.is_processing = True
        
        # Show progress bar
        self.progress_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=(0, 5), before=self.root.winfo_children()[-1])
        
        def progress_callback(current, total, message):
            self.matcher_log(f"[{current}/{total}] {message}")
            
            # Update progress bar in main thread
            if total > 0:
                percentage = (current / total) * 100
                self.root.after(0, lambda: self.progress_bar.config(value=percentage))
                self.root.after(0, lambda: self.progress_label.config(text=f"{current:,}/{total:,} - {message}"))
        
        def run_matching():
            if method == "file":
                self.matcher_log(f"Input image: {os.path.basename(actual_image_path)}")
            elif method == "url":
                self.matcher_log(f"Input URL: {input_image}")
            elif method == "wiki":
                self.matcher_log(f"Hypixel Wiki: {input_image}")
            
            self.matcher_log(f"Search directory: {search_dir}")
            
            # Map algorithm dropdown to internal name
            algo_map = {
                "Render to Skin (Convert+Match) 🎯": "render_to_skin",
                "Render Match (3D→2D) ⭐": "render_match",
                "Balanced (Default)": "balanced",
                "Skin-Optimized": "skin_optimized",
                "AI Perceptual (ResNet18)": "ai_perceptual",
                "AI Mobile (ResNet50)": "ai_mobile",
                "Deep Features": "deep_features",
                "Color Distribution": "color_distribution",
                "Fast Match": "fast"
            }
            algorithm = algo_map.get(self.algorithm_choice.get(), "balanced")
            self.debug_log(f"Using algorithm: {algorithm}")
            self.matcher_log(f"Algorithm: {self.algorithm_choice.get()}")
            self.matcher_log(f"Finding top {self.top_n_matches.get()} matches...\n")
            
            try:
                matches, error = find_matching_skins(
                    actual_image_path,
                    search_dir,
                    top_n=self.top_n_matches.get(),
                    algorithm=algorithm,
                    progress_callback=progress_callback,
                    cancel_check=lambda: self.should_cancel
                )
            except Exception as e:
                self.is_processing = False
                self.match_btn.config(state=tk.NORMAL)
                self.match_cancel_btn.config(state=tk.DISABLED)
                
                # Hide progress bar
                self.root.after(0, lambda: self.progress_frame.pack_forget())
                self.root.after(0, lambda: self.progress_bar.config(value=0))
                self.root.after(0, lambda: self.progress_label.config(text=""))
                
                error_msg = f"Matching failed: {type(e).__name__}: {e}"
                print(f"[ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", error_msg)
                self.matcher_log(f"\n❌ Error: {error_msg}")
                return
            
            self.is_processing = False
            
            if self.should_cancel:
                self.matcher_log("\n❌ Operation cancelled by user")
                messagebox.showinfo("Cancelled", "Matching operation was cancelled.")
            elif error:
                messagebox.showerror("Error", error)
                self.matcher_log(f"\nError: {error}")
            elif matches:
                self.matcher_log(f"\n{'='*50}")
                self.matcher_log(f"Found {len(matches)} matches!")
                self.matcher_log(f"{'='*50}\n")
                
                for i, (distance, path, metrics) in enumerate(matches, 1):
                    self.matcher_log(f"{i}. {os.path.basename(path)}")
                    
                    # Format metrics based on what's available
                    metric_parts = [f"Distance: {distance:.6f}"]
                    
                    if 'hash_dist' in metrics:
                        metric_parts.append(f"Hash: {metrics['hash_dist']:.1f}")
                    if 'color_dist' in metrics:
                        metric_parts.append(f"Colors: {metrics['color_dist']:.4f}")
                    if 'hist_dist' in metrics:
                        metric_parts.append(f"Hist: {metrics['hist_dist']:.4f}")
                    if 'texture_dist' in metrics:
                        metric_parts.append(f"Texture: {metrics['texture_dist']:.4f}")
                    if 'edge_dist' in metrics:
                        metric_parts.append(f"Edges: {metrics['edge_dist']:.4f}")
                    if 'ssim_dist' in metrics:
                        metric_parts.append(f"SSIM: {metrics['ssim_dist']:.4f}")
                    if 'dim_match' in metrics:
                        metric_parts.append(f"DimMatch: {metrics['dim_match']:.2f}")
                    if 'ai_dist' in metrics:
                        metric_parts.append(f"AI: {metrics['ai_dist']:.4f}")
                    if 'mobile_dist' in metrics:
                        metric_parts.append(f"Mobile: {metrics['mobile_dist']:.4f}")
                    if 'palette_dist' in metrics:
                        metric_parts.append(f"Palette: {metrics['palette_dist']:.4f}")
                    if 'spatial_dist' in metrics:
                        metric_parts.append(f"Spatial: {metrics['spatial_dist']:.4f}")
                    if 'ai_unavailable' in metrics:
                        metric_parts.append(f"AI: N/A (PyTorch not installed)")
                    if 'mobile_unavailable' in metrics:
                        metric_parts.append(f"Mobile: N/A (PyTorch not installed)")
                    
                    self.matcher_log(f"   {' | '.join(metric_parts)}")
                
                # Copy matches to output
                output_dir = os.path.join(os.getcwd(), "output")
                copied = copy_skin_files(matches, output_dir, clear_existing=True)
                
                self.matcher_log(f"\n✅ Copied {len(copied)} matches to: {output_dir}")
                self.last_output_dir = output_dir
                self.view_matches_btn.config(state=tk.NORMAL)
                
                messagebox.showinfo("Success", f"Found and copied {len(matches)} matching skins!")
            
            self.match_btn.config(state=tk.NORMAL)
            self.match_cancel_btn.config(state=tk.DISABLED)
            
            # Hide progress bar
            self.root.after(0, lambda: self.progress_frame.pack_forget())
            self.root.after(0, lambda: self.progress_bar.config(value=0))
            self.root.after(0, lambda: self.progress_label.config(text=""))
            
            # Clean up temporary image if it was downloaded
            if self.temp_downloaded_image and os.path.exists(self.temp_downloaded_image):
                try:
                    os.remove(self.temp_downloaded_image)
                    self.temp_downloaded_image = None
                except:
                    pass  # Ignore cleanup errors
        
        # Run in separate thread
        thread = threading.Thread(target=run_matching, daemon=True)
        thread.start()
    
    def cancel_matching(self):
        if self.is_processing:
            self.should_cancel = True
            self.matcher_log("\n*** Cancellation requested ***")
            self.match_cancel_btn.config(state=tk.DISABLED)
    
    def view_match_results(self):
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            ImageViewerWindow(self.root, self.last_output_dir)
        else:
            messagebox.showwarning("No Results", "No match results available to view.")
    
    # Copier tab methods
    def check_for_existing_output(self):
        """Check if output directory exists for current input folder."""
        folder = self.folder_path.get()
        if folder:
            potential_output = f"{folder}_png"
            if os.path.exists(potential_output) and os.path.isdir(potential_output):
                self.last_output_dir = potential_output
    
    def update_viewer_button_state(self):
        """Update the viewer button text and state based on available directories."""
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            self.viewer_btn.config(text="View Output Images", state=tk.NORMAL)
        elif self.folder_path.get() and os.path.exists(self.folder_path.get()):
            self.viewer_btn.config(text="View Input Images", state=tk.NORMAL)
        else:
            self.viewer_btn.config(text="View Images", state=tk.DISABLED)
    
    def browse_folder(self):
        initial_dir = os.getcwd()
        folder = filedialog.askdirectory(title="Select Input Folder", initialdir=initial_dir)
        if folder:
            self.folder_path.set(folder)
            self.check_for_existing_output()
            self.update_viewer_button_state()
    
    def on_input_method_change(self):
        """Update UI based on selected input method."""
        method = self.input_method.get()
        self.debug_log(f"Input method changed to: {method}")
        
        # Remove focus from entry field
        self.root.focus()
        
        if method == "file":
            self.browse_img_btn.config(text="Browse...", state=tk.NORMAL)
            self.input_image_entry.config(state=tk.NORMAL, fg='black')
            self.input_image_path.set("")
        elif method == "url":
            self.browse_img_btn.config(text="Browse...", state=tk.DISABLED)
            self.input_image_entry.config(state=tk.NORMAL)
            self.input_image_path.set("")
            # Show placeholder hint
            self.input_image_entry.delete(0, tk.END)
            self.input_image_entry.insert(0, "Enter image URL (e.g., https://example.com/skin.png)")
            self.input_image_entry.config(fg='gray')
            self.input_image_entry.bind('<FocusIn>', self._clear_url_placeholder)
            self.input_image_entry.bind('<FocusOut>', self._restore_url_placeholder)
        elif method == "wiki":
            self.browse_img_btn.config(text="Browse...", state=tk.DISABLED)
            self.input_image_entry.config(state=tk.NORMAL)
            self.input_image_path.set("")
            # Show placeholder hint
            self.input_image_entry.delete(0, tk.END)
            self.input_image_entry.insert(0, "Enter Hypixel Wiki URL (e.g., https://wiki.hypixel.net/Minos_Inquisitor)")
            self.input_image_entry.config(fg='gray')
            self.input_image_entry.bind('<FocusIn>', self._clear_url_placeholder)
            self.input_image_entry.bind('<FocusOut>', self._restore_url_placeholder)
        
        # Update preview to show placeholder when method changes
        self.update_input_preview()
    
    def show_input_preview_window(self):
        """Show input image in a popup window."""
        if not self.input_preview_image:
            messagebox.showwarning("No Image", "No image available to preview.")
            return
        
        # Create popup window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Input Image Preview")
        preview_window.geometry("600x600")
        preview_window.transient(self.root)
        
        # Create frame with scrollbars
        frame = ttk.Frame(preview_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add canvas for scrolling
        canvas = tk.Canvas(frame, bg='white')
        v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
        
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Display image
        img = self.input_preview_image.copy()
        
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        photo = ImageTk.PhotoImage(img)
        
        # Create image on canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo  # Keep reference
        
        # Configure scroll region
        canvas.configure(scrollregion=canvas.bbox(tk.ALL))
        
        # Add image info
        info_label = ttk.Label(
            preview_window,
            text=f"Size: {img.width}x{img.height} pixels",
            font=('Arial', 9)
        )
        info_label.pack(pady=5)
        
        # Center window on screen
        preview_window.update_idletasks()
        x = (preview_window.winfo_screenwidth() // 2) - (preview_window.winfo_width() // 2)
        y = (preview_window.winfo_screenheight() // 2) - (preview_window.winfo_height() // 2)
        preview_window.geometry(f"+{x}+{y}")
    
    def show_input_preview_window(self):
        """Show input image in a popup window."""
        if not self.input_preview_image:
            messagebox.showwarning("No Image", "No image available to preview.")
            return
        
        # Create popup window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Input Image Preview")
        preview_window.configure(bg=self.colors['bg'])
        preview_window.geometry("650x650")
        preview_window.transient(self.root)
        
        # Main frame
        main_frame = tk.Frame(preview_window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title_label = tk.Label(main_frame,
                               text="Input Image Preview",
                               font=("Segoe UI", 14, "bold"),
                               bg=self.colors['bg'],
                               fg=self.colors['text'])
        title_label.pack(pady=(0, 10))
        
        # Image info
        img = self.input_preview_image
        info_text = f"Size: {img.width}×{img.height} pixels | Mode: {img.mode}"
        info_label = tk.Label(main_frame,
                             text=info_text,
                             font=("Segoe UI", 9),
                             bg=self.colors['bg'],
                             fg=self.colors['text_secondary'])
        info_label.pack(pady=(0, 10))
        
        # Image container with scrollbars
        container = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.SOLID, borderwidth=1)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        canvas = tk.Canvas(container, bg='white', highlightthickness=0)
        v_scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        h_scrollbar = tk.Scrollbar(container, orient=tk.HORIZONTAL, command=canvas.xview)
        
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Prepare image for display
        display_img = img.copy()
        if display_img.mode == 'RGBA':
            # Create checkerboard background for transparency
            bg = Image.new('RGB', display_img.size, (255, 255, 255))
            bg.paste(display_img, mask=display_img.split()[3])
            display_img = bg
        elif display_img.mode != 'RGB':
            display_img = display_img.convert('RGB')
        
        # Create PhotoImage
        photo = ImageTk.PhotoImage(display_img)
        
        # Display image on canvas
        canvas.create_image(10, 10, anchor=tk.NW, image=photo)
        canvas.image = photo  # Keep reference
        
        # Configure scroll region
        canvas.configure(scrollregion=(0, 0, display_img.width + 20, display_img.height + 20))
        
        # Close button
        close_btn = tk.Button(main_frame,
                             text="Close",
                             command=preview_window.destroy,
                             font=("Segoe UI", 10),
                             bg=self.colors['primary'],
                             fg='white',
                             activebackground=self.colors['primary_dark'],
                             activeforeground='white',
                             relief=tk.FLAT,
                             cursor="hand2",
                             padx=30,
                             pady=8)
        close_btn.pack(pady=(10, 0))
        self._add_button_hover(close_btn, self.colors['primary_dark'], 'white', flat=True)
        
        # Center window on screen
        preview_window.update_idletasks()
        x = (preview_window.winfo_screenwidth() // 2) - (preview_window.winfo_width() // 2)
        y = (preview_window.winfo_screenheight() // 2) - (preview_window.winfo_height() // 2)
        preview_window.geometry(f"+{x}+{y}")
    
    def _clear_url_placeholder(self, event):
        """Clear placeholder text on focus."""
        if self.input_image_entry.cget('fg') == 'gray':
            self.input_image_entry.delete(0, tk.END)
            self.input_image_entry.config(fg='black')
    
    def _restore_url_placeholder(self, event):
        """Restore placeholder text if empty."""
        if not self.input_image_path.get():
            method = self.input_method.get()
            if method == "url":
                self.input_image_entry.insert(0, "Enter image URL (e.g., https://example.com/skin.png)")
                self.input_image_entry.config(fg='gray')
            elif method == "wiki":
                self.input_image_entry.insert(0, "Enter Hypixel Wiki URL (e.g., https://wiki.hypixel.net/Minos_Inquisitor)")
                self.input_image_entry.config(fg='gray')
    
    def on_algorithm_change(self, event=None):
        """Handle algorithm selection change."""
        selected = self.algorithm_choice.get()
        self.debug_log(f"Algorithm changed to: {selected}")
        
        # Show/hide AI test button based on selection
        if "AI Perceptual" in selected or "AI Mobile" in selected:
            self.ai_test_btn.pack(side=tk.LEFT, padx=8)
        else:
            self.ai_test_btn.pack_forget()
        
        # Show/hide preview button for render_to_skin algorithm
        if "Render to Skin" in selected and "Convert" in selected:
            input_path = self.input_image_path.get()
            if input_path and os.path.exists(input_path):
                self.preview_btn.pack(side=tk.LEFT, padx=8)
                self.preview_btn.config(state=tk.NORMAL)
            else:
                self.preview_btn.pack(side=tk.LEFT, padx=8)
                self.preview_btn.config(state=tk.DISABLED)
        else:
            self.preview_btn.pack_forget()
    
    def test_ai_availability(self):
        """Test if PyTorch is available and AI algorithm is working."""
        self.debug_log("Testing AI availability...")
        
        try:
            # Import here to test availability
            import torch
            import torchvision.models as models
            
            result_parts = ["✅ PyTorch Test Results:\n"]
            result_parts.append(f"✓ PyTorch version: {torch.__version__}")
            result_parts.append(f"✓ Torchvision installed: Yes")
            
            # Test model loading
            try:
                result_parts.append("\n🔄 Loading ResNet18 model...")
                test_model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
                result_parts.append("✓ ResNet18 loaded successfully")
                
                # Test feature extraction
                result_parts.append("\n🔄 Testing feature extraction...")
                from utils.image_matcher import extract_ai_features
                from PIL import Image
                import numpy as np
                
                # Create a test image
                test_img = Image.fromarray(np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8))
                features = extract_ai_features(test_img)
                
                if features is not None:
                    result_parts.append(f"✓ Feature extraction working (512-dimensional vector)")
                    result_parts.append("\n🎉 AI Perceptual algorithm is FULLY OPERATIONAL!")
                    result_parts.append("\nThe algorithm will use deep learning features for matching.")
                    
                    messagebox.showinfo("AI Test - SUCCESS", "\n".join(result_parts))
                else:
                    result_parts.append("⚠️ Feature extraction failed")
                    result_parts.append("\n⚠️ AI will use fallback mode (color + histogram)")
                    messagebox.showwarning("AI Test - Partial", "\n".join(result_parts))
                    
            except Exception as e:
                result_parts.append(f"\n❌ Model loading failed: {str(e)}")
                result_parts.append("\n⚠️ AI will use fallback mode (color + histogram)")
                messagebox.showwarning("AI Test - Partial", "\n".join(result_parts))
                
        except ImportError as e:
            error_msg = """❌ PyTorch NOT Installed

PyTorch is required for the AI Perceptual algorithm.

Current status:
• The algorithm will use FALLBACK mode
• Fallback uses: color matching + histogram
• Results will be less accurate

To enable full AI features:

📦 Install PyTorch (CPU version - recommended):
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

Or GPU version (if you have NVIDIA GPU):
   pip install torch torchvision

After installation, restart the application."""
            
            messagebox.showerror("AI Test - PyTorch Not Found", error_msg)
            self.debug_log(f"PyTorch import failed: {str(e)}")
    
    def show_algorithm_info(self, event=None):
        """Show information about matching algorithms."""
        info_text = """🔍 Matching Algorithms:

🎯 Render to Skin (Convert+Match) - NEW & MOST ACCURATE!
BEST FOR 3D RENDERS! First converts your 3D render to a 2D skin using region detection and pixel extraction (same as Converter tab), then compares ONLY the visible regions (front, top, left) pixel-by-pixel. This gives the most accurate matches because it directly compares textures that are actually visible in the render. Slightly slower than Render Match but much more accurate!

⭐ Render Match (3D→2D) - FAST FOR RENDERS
SPECIFICALLY DESIGNED for matching 3D rendered characters to 2D skin files! Extracts 24 dominant colors ignoring lighting/shading, analyzes spatial color patterns in a 4x4 grid. Does NOT use neural networks - uses color palette matching (70%) + spatial patterns (30%). FAST and designed for this exact problem!

🎯 Balanced (Default)
Optimal for most cases. Uses dominant colors (60%), color histogram (35%), and perceptual hashing (5%). Best general-purpose algorithm.

🎨 Skin-Optimized
Designed for Minecraft skins. Detects 64x64/64x32 textures, analyzes texture patterns, and focuses on skin-specific features. Best for finding exact skin matches.

🤖 AI Perceptual (ResNet18)
Uses ResNet18 deep learning for feature extraction. Focuses on deep semantic features (50%), colors (35%), and histogram (15%). Good for general image matching. Requires PyTorch + GPU.

📱 AI Mobile (ResNet50)
Uses ResNet50 (deeper than ResNet18) with FP16 for texture matching. Extracts 2048-dim features with multi-scale processing. Requires PyTorch + GPU.

🔬 Deep Features
Uses edge detection and structural similarity (SSIM). Focuses on shapes and patterns rather than colors. Good for similar armor/clothing styles.

🌈 Color Distribution
Emphasizes overall color presence over exact placement. Best when rendered pose/angle differs significantly from skin layout.

⚡ Fast Match
Quick color-based matching using smaller histograms. Faster but less accurate. Good for large datasets (10,000+ files).

💡 Tip: Try Render to Skin first for best accuracy, or Render Match if you need speed!"""
        
        messagebox.showinfo("Algorithm Information", info_text)
    
    def on_input_path_changed(self):
        """Enable/disable preview button based on input path and algorithm."""
        selected = self.algorithm_choice.get()
        input_path = self.input_image_path.get()
        
        # Update image preview
        self.update_input_preview()
        
        # Only show preview button for render_to_skin algorithm
        if "Render to Skin" in selected and "Convert" in selected:
            if input_path and os.path.exists(input_path):
                self.preview_btn.config(state=tk.NORMAL)
                self.preview_btn.pack(side=tk.LEFT, padx=8)
            else:
                self.preview_btn.config(state=tk.DISABLED)
                self.preview_btn.pack(side=tk.LEFT, padx=8)
        else:
            self.preview_btn.pack_forget()
    
    def update_input_preview(self):
        """Update the input image preview data and enable/disable preview button."""
        method = self.input_method.get()
        input_value = self.input_image_path.get()
        
        # Clear placeholder text if present
        if self.input_image_entry.cget('fg') == 'gray':
            input_value = ""
        
        # Clear previous preview
        self.input_preview_image = None
        
        if not input_value:
            # No input - disable button
            self.preview_input_btn.config(state=tk.DISABLED)
            return
        
        try:
            img = None
            
            if method == "file":
                # Local file
                if os.path.exists(input_value):
                    img = Image.open(input_value)
                else:
                    self.preview_input_btn.config(state=tk.DISABLED)
                    return
            
            elif method == "url":
                # Direct URL - download and cache
                try:
                    img = download_image_from_url(input_value, debug_callback=self.debug_log)
                except Exception as e:
                    self.preview_input_btn.config(state=tk.DISABLED)
                    return
            
            elif method == "wiki":
                # Hypixel wiki - parse and get sprite head icon
                try:
                    img = parse_wiki_for_image(input_value, debug_callback=self.debug_log)
                except Exception as e:
                    self.preview_input_btn.config(state=tk.DISABLED)
                    return
            
            if img:
                # Store the image for preview window
                self.input_preview_image = img
                self.preview_input_btn.config(state=tk.NORMAL)
        
        except Exception as e:
            self.debug_log(f"Error loading input preview: {str(e)}")
            self.preview_input_btn.config(state=tk.DISABLED)
    
    def preview_converted_image(self):
        """Show a preview of the converted input image."""
        input_path = self.input_image_path.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "No valid input image selected!")
            return
        
        try:
            # Import the conversion function
            from utils.image_matcher import convert_render_to_skin
            
            # Load the image
            img = Image.open(input_path)
            
            # Check if it's already a skin or needs conversion
            if img.size == (64, 64):
                preview_img = img
                title = "Input Image (Already 64x64 Skin Format)"
            else:
                # Convert render to skin
                preview_img = convert_render_to_skin(img)
                title = "Converted Input Image (3D Render → 2D Skin)"
            
            # Create a preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title(title)
            preview_window.configure(bg=self.colors['bg'])
            preview_window.geometry("400x500")
            
            # Info label
            info_label = tk.Label(preview_window,
                                text=title,
                                font=("Segoe UI", 11, "bold"),
                                bg=self.colors['bg'],
                                fg=self.colors['text'])
            info_label.pack(pady=10)
            
            # Show the image (scaled up for visibility)
            scale = 4  # Scale 64x64 to 256x256
            display_img = preview_img.resize((64*scale, 64*scale), Image.NEAREST)
            photo = ImageTk.PhotoImage(display_img)
            
            img_label = tk.Label(preview_window, image=photo, bg=self.colors['bg'])
            img_label.image = photo  # Keep a reference
            img_label.pack(pady=10)
            
            # Description
            if img.size == (64, 64):
                desc = "This image is already in 64x64 skin format.\nNo conversion needed."
            else:
                desc = f"Original size: {img.size[0]}x{img.size[1]}\n"
                desc += "Converted to 64x64 skin format using region detection.\n"
                desc += "Only visible regions (front/top/left) will be compared."
            
            desc_label = tk.Label(preview_window,
                                text=desc,
                                font=("Segoe UI", 9),
                                bg=self.colors['bg'],
                                fg=self.colors['text_secondary'],
                                justify=tk.CENTER)
            desc_label.pack(pady=10)
            
            # Close button
            close_btn = tk.Button(preview_window,
                                text="Close",
                                command=preview_window.destroy,
                                font=("Segoe UI", 10),
                                bg=self.colors['primary'],
                                fg="white",
                                relief=tk.FLAT,
                                padx=20,
                                pady=8,
                                cursor="hand2")
            close_btn.pack(pady=10)
            self._add_button_hover(close_btn, self.colors['primary_dark'], 'white', flat=True)
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to preview image:\n{str(e)}")
            self.debug_log(f"Preview error: {str(e)}")
    
    def open_discord(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("soulreturns")
            messagebox.showinfo("Discord", "Discord username 'soulreturns' copied to clipboard!")
        except:
            messagebox.showinfo("Discord", "Discord username: soulreturns")
    
    def open_image_viewer(self):
        # Prefer output folder if available, otherwise use input folder
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            folder = self.last_output_dir
        else:
            folder = self.folder_path.get()
        
        if not folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder to view images from.")
            return
        
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Folder does not exist: {folder}")
            return
        
        # Open the image viewer
        ImageViewerWindow(self.root, folder)
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def cancel_process(self):
        if self.is_processing:
            self.should_cancel = True
            self.log("\n*** Cancellation requested - cleaning up... ***")
            self.cancel_btn.config(state=tk.DISABLED)
    
    def process_folder(self):
        self.debug_log("=== Process Folder Started ===")
        folder = self.folder_path.get()
        self.debug_log(f"Input folder: {folder}")
        
        if not folder:
            self.debug_log("No folder selected")
            messagebox.showwarning("No Folder Selected", "Please select an input folder first.")
            return
        
        # Check if output directory already exists
        output_dir = f"{folder}_png"
        if os.path.exists(output_dir):
            response = messagebox.askyesno(
                "Output Folder Exists",
                f"The output folder '{output_dir}' already exists.\n\nDo you want to overwrite it?",
                icon='warning'
            )
            if not response:
                self.log("Operation cancelled by user - output folder already exists.\n")
                return
            else:
                # Remove existing directory
                try:
                    self.log(f"Removing existing folder: {output_dir}")
                    import shutil
                    shutil.rmtree(output_dir)
                    self.log("Existing folder removed.\n")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to remove existing folder:\n{e}")
                    return
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Reset cancel flag and store output directory
        self.should_cancel = False
        self.current_output_dir = output_dir
        
        # Update button states
        self.process_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.is_processing = True
        
        def run_process():
            self.log(f"Starting to process folder: {folder}")
            self.log(f"Output folder: {output_dir}\n")
            
            success = copy_and_rename_to_png(
                folder,
                output_dir=output_dir,
                merge_files=self.merge_files.get(),
                log_callback=self.log,
                cancel_check=lambda: self.should_cancel
            )
            
            self.is_processing = False
            
            if self.should_cancel:
                # Clean up output directory
                self.log("\nCancelled - removing output directory...")
                try:
                    if os.path.exists(self.current_output_dir):
                        import shutil
                        shutil.rmtree(self.current_output_dir)
                        self.log(f"Output directory '{self.current_output_dir}' removed.")
                    messagebox.showinfo("Cancelled", "Operation cancelled and output directory removed.")
                except Exception as e:
                    self.log(f"Error removing output directory: {e}")
                    messagebox.showerror("Error", f"Operation cancelled but failed to remove output directory:\n{e}")
            elif success:
                self.last_output_dir = output_dir
                self.update_viewer_button_state()
                messagebox.showinfo("Success", f"Files copied successfully!\nOutput: {output_dir}")
            else:
                messagebox.showerror("Error", "Failed to copy files. Check the log for details.")
            
            self.process_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.current_output_dir = None
        
        # Run in separate thread to keep GUI responsive
        thread = threading.Thread(target=run_process, daemon=True)
        thread.start()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description=f"{__app_name__} v{__version__}")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose debug output')
    args = parser.parse_args()
    
    # Set global DEBUG flag
    DEBUG = args.verbose
    
    if DEBUG:
        print("[DEBUG] Verbose mode enabled")
        print(f"[DEBUG] Starting {__app_name__} v{__version__}")
    
    root = tk.Tk()
    app = SkinCopierGUI(root, verbose=args.verbose)
    
    if DEBUG:
        print("[DEBUG] GUI initialized, starting mainloop...")
    
    root.mainloop()
    
    if DEBUG:
        print("[DEBUG] Application closed")
