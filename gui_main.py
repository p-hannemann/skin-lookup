"""
Main GUI application for Skin Copier with integrated skin matching.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
from pathlib import Path
import subprocess
import urllib.request
import io
from PIL import Image, ImageTk

from file_utils import copy_and_rename_to_png
from skin_matcher import find_matching_skins, copy_skin_files
from image_viewer import ImageViewerWindow


class SkinCopierGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Skin Copier & Matcher")
        self.root.geometry("850x600")
        self.root.resizable(True, True)
        self.is_processing = False
        self.should_cancel = False
        self.current_output_dir = None
        self.last_output_dir = None
        self.preview_window = None
        self.example_image_url = "https://www.minecraftskins.com/uploads/preview-skins/2022/03/22/minos-inquisitor-20083594.png"
        
        # Modern color scheme
        self.colors = {
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
        
        # Configure root background
        self.root.configure(bg=self.colors['bg'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure('TNotebook.Tab', 
                       padding=[20, 10], 
                       font=('Segoe UI', 10),
                       background=self.colors['card'],
                       borderwidth=0,
                       width=15)
        style.map('TNotebook.Tab', 
                 background=[('selected', self.colors['card']), ('!selected', self.colors['card'])],
                 foreground=[('selected', self.colors['primary']), ('!selected', self.colors['text'])],
                 borderwidth=[('selected', 0), ('!selected', 0)],
                 padding=[('selected', [20, 10]), ('!selected', [20, 10])])
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_matcher_tab()
        self.create_copier_tab()
        
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
    
    def create_matcher_tab(self):
        """Create the skin matcher tab."""
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
        
        img_frame = tk.Frame(frame_input, bg=self.colors['card'])
        img_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.input_image_path = tk.StringVar()
        entry = tk.Entry(img_frame, 
                        textvariable=self.input_image_path, 
                        font=("Segoe UI", 10),
                        relief=tk.SOLID,
                        borderwidth=1)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        
        browse_img_btn = tk.Button(img_frame, 
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
        browse_img_btn.pack(side=tk.RIGHT)
        self._add_button_hover(browse_img_btn, self.colors['primary'], '#ffffff')
        
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
        """Add hover effect to a button."""
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
    
    def browse_input_image(self):
        initial_dir = os.getcwd()
        file_path = filedialog.askopenfilename(
            title="Select Input Image",
            initialdir=initial_dir,
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            self.input_image_path.set(file_path)
    
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
    
    def find_matches(self):
        input_image = self.input_image_path.get()
        search_dir = self.search_dir_path.get()
        
        if not input_image:
            messagebox.showwarning("No Image Selected", "Please select an input image.")
            return
        
        if not search_dir:
            messagebox.showwarning("No Directory Selected", "Please select a search directory.")
            return
        
        if not os.path.exists(input_image):
            messagebox.showerror("Error", f"Input image does not exist: {input_image}")
            return
        
        if not os.path.exists(search_dir):
            messagebox.showerror("Error", f"Search directory does not exist: {search_dir}")
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
        
        def progress_callback(current, total, message):
            self.matcher_log(f"[{current}/{total}] {message}")
        
        def run_matching():
            self.matcher_log(f"Input image: {os.path.basename(input_image)}")
            self.matcher_log(f"Search directory: {search_dir}")
            self.matcher_log(f"Finding top {self.top_n_matches.get()} matches...\n")
            
            matches, error = find_matching_skins(
                input_image,
                search_dir,
                top_n=self.top_n_matches.get(),
                progress_callback=progress_callback
            )
            
            self.is_processing = False
            
            if error:
                messagebox.showerror("Error", error)
                self.matcher_log(f"\nError: {error}")
            elif matches:
                self.matcher_log(f"\n{'='*50}")
                self.matcher_log(f"Found {len(matches)} matches!")
                self.matcher_log(f"{'='*50}\n")
                
                for i, (distance, path, metrics) in enumerate(matches, 1):
                    self.matcher_log(f"{i}. {os.path.basename(path)}")
                    self.matcher_log(f"   Distance: {distance:.6f} | Hash: {metrics['hash_dist']:.1f} | Colors: {metrics['color_dist']:.4f}")
                
                # Copy matches to output
                output_dir = os.path.join(os.getcwd(), "output")
                copied = copy_skin_files(matches, output_dir, clear_existing=True)
                
                self.matcher_log(f"\n✅ Copied {len(copied)} matches to: {output_dir}")
                self.last_output_dir = output_dir
                self.view_matches_btn.config(state=tk.NORMAL)
                
                messagebox.showinfo("Success", f"Found and copied {len(matches)} matching skins!")
            
            self.match_btn.config(state=tk.NORMAL)
            self.match_cancel_btn.config(state=tk.DISABLED)
        
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
    
    # Copier tab methods (existing functionality)
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
        folder = self.folder_path.get()
        
        if not folder:
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
    root = tk.Tk()
    app = SkinCopierGUI(root)
    root.mainloop()
