"""
Image viewer window for browsing images in a directory.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import threading
import subprocess
import traceback
from PIL import Image, ImageTk

# Check for verbose mode
VERBOSE = '--verbose' in sys.argv or '-v' in sys.argv

def debug_print(*args, **kwargs):
    """Print debug messages if verbose mode is enabled."""
    if VERBOSE:
        print("[DEBUG]", *args, **kwargs)


class ImageViewerWindow:
    def __init__(self, parent, directory):
        try:
            debug_print("Initializing ImageViewerWindow")
            self.window = tk.Toplevel(parent)
            self.window.title("Image Viewer - Loading...")
            self.window.geometry("800x600")
            
            self.directory = directory
            debug_print(f"Directory: {directory}")
            self.image_files = []
            self.all_files_data = []  # Store (path, creation_time, modification_time)
            self.folder_structure = {}  # Store folder hierarchy
            self.folder_to_tree_item = {}  # Map folder paths to tree items
            self.current_index = 0
            self.loading = True
            self.sort_method = tk.StringVar(value="path")  # Default sort
            self._updating_tree_selection = False  # Flag to prevent recursion
            debug_print("Variables initialized")
        except Exception as e:
            debug_print(f"Error in __init__: {e}")
            traceback.print_exc()
            raise
        
        try:
            # Setup UI first
            debug_print("Setting up UI")
            self.setup_ui()
            
            # Show loading message
            debug_print("Showing loading message")
            self.image_label.config(text="Loading images...\nPlease wait...", 
                                   fg="white", font=("Arial", 14, "bold"))
            
            # Collect images in background thread to avoid freezing
            debug_print("Starting background thread")
            thread = threading.Thread(target=self.collect_images_background, daemon=True)
            thread.start()
        except Exception as e:
            debug_print(f"Error in setup: {e}")
            traceback.print_exc()
            raise
    
    def collect_images_background(self):
        """Collect all image files from directory recursively in background."""
        try:
            debug_print("Starting image collection")
            # Common image extensions, including files without extensions
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', ''}
            temp_files_data = []
            count = 0
            
            for root, dirs, files in os.walk(self.directory):
                for file in files:
                    file_path = Path(root) / file
                    # Quick check: just verify extension, don't open every file
                    if file_path.suffix.lower() in image_extensions:
                        try:
                            stats = file_path.stat()
                            temp_files_data.append((file_path, stats.st_ctime, stats.st_mtime))
                            count += 1
                            # Update progress every 100 files
                            if count % 100 == 0:
                                debug_print(f"Found {count} images")
                                self.window.after(0, lambda c=count: self.update_loading_status(c))
                        except Exception as e:
                            debug_print(f"Error reading file {file_path}: {e}")
                            # Skip files with permission errors
                            pass
            
            debug_print(f"Total images found: {count}")
            # Store all data and apply initial sort
            self.all_files_data = temp_files_data
            debug_print("Applying sort")
            self.apply_sort()
            
            # Build folder structure
            debug_print("Building folder structure")
            self.build_folder_structure()
            
            # Notify completion on main thread
            debug_print("Images loaded, notifying main thread")
            self.window.after(0, self.on_images_loaded)
        except Exception as e:
            debug_print(f"Error in collect_images_background: {e}")
            traceback.print_exc()
    
    def apply_sort(self):
        """Apply the current sort method to the image files."""
        if not self.all_files_data:
            return
        
        sort = self.sort_method.get()
        
        if sort == "path":
            # Sort by path (default)
            sorted_data = sorted(self.all_files_data, key=lambda x: x[0])
        elif sort == "created_desc":
            # Newest first
            sorted_data = sorted(self.all_files_data, key=lambda x: x[1], reverse=True)
        elif sort == "created_asc":
            # Oldest first
            sorted_data = sorted(self.all_files_data, key=lambda x: x[1])
        elif sort == "modified_desc":
            # Newest modified first
            sorted_data = sorted(self.all_files_data, key=lambda x: x[2], reverse=True)
        elif sort == "modified_asc":
            # Oldest modified first
            sorted_data = sorted(self.all_files_data, key=lambda x: x[2])
        else:
            sorted_data = sorted(self.all_files_data, key=lambda x: x[0])
        
        # Extract just the paths
        self.image_files = [path for path, _, _ in sorted_data]
    
    def on_sort_changed(self, value=None):
        """Handle sort method change."""
        if self.loading:
            return
        
        # Remember current file
        current_file = self.image_files[self.current_index] if self.image_files else None
        
        # Re-sort
        self.apply_sort()
        
        # Try to find the same file in new order
        if current_file and current_file in self.image_files:
            self.current_index = self.image_files.index(current_file)
        else:
            self.current_index = 0
        
        # Refresh display
        self.show_current_image()
    
    def update_loading_status(self, count):
        """Update loading message with count."""
        self.image_label.config(text=f"Loading images...\nFound {count} images so far...")
    
    def build_folder_structure(self):
        """Build folder hierarchy for tree view."""
        try:
            debug_print("Building folder structure")
            self.folder_structure = {}
            
            for file_path in self.image_files:
                folder = file_path.parent
                if folder not in self.folder_structure:
                    self.folder_structure[folder] = []
                self.folder_structure[folder].append(file_path)
            
            debug_print(f"Built structure with {len(self.folder_structure)} folders")
        except Exception as e:
            debug_print(f"Error in build_folder_structure: {e}")
            traceback.print_exc()
            raise
    
    def populate_tree(self):
        """Populate the folder tree view."""
        try:
            debug_print("Populating tree view")
            # Clear existing items
            for item in self.folder_tree.get_children():
                self.folder_tree.delete(item)
            
            # Get all unique folders sorted
            folders = sorted(self.folder_structure.keys())
            debug_print(f"Populating {len(folders)} folders")
            
            # Create tree structure
            root_path = Path(self.directory)
            self.folder_to_tree_item = {}  # Map folder paths to tree items
            
            for folder in folders:
                # Get relative path from root
                try:
                    rel_path = folder.relative_to(root_path)
                except ValueError:
                    rel_path = folder
                
                parts = rel_path.parts if rel_path.parts else (folder.name,)
                
                # Build tree hierarchy
                parent_id = ""
                current_path = root_path
                
                for i, part in enumerate(parts):
                    current_path = current_path / part
                    path_key = str(current_path)
                    
                    if path_key not in self.folder_to_tree_item:
                        # Count images in this folder
                        img_count = len(self.folder_structure.get(current_path, []))
                        label = f"{part} ({img_count})" if img_count > 0 else part
                        
                        tree_item = self.folder_tree.insert(
                            parent_id, "end", 
                            text=label,
                            values=[str(current_path)],
                            open=(i == 0)  # Open first level by default
                        )
                        self.folder_to_tree_item[path_key] = tree_item
                    
                    parent_id = self.folder_to_tree_item[path_key]
            
            debug_print("Tree populated successfully")
        except Exception as e:
            debug_print(f"Error in populate_tree: {e}")
            traceback.print_exc()
            raise
    
    def update_tree_selection(self):
        """Update tree view to select the folder of the current image."""
        if not self.image_files or self.loading or not hasattr(self, 'folder_to_tree_item'):
            return
        
        current_image = self.image_files[self.current_index]
        current_folder = current_image.parent
        path_key = str(current_folder)
        
        # Find and select the tree item for this folder
        if path_key in self.folder_to_tree_item:
            tree_item = self.folder_to_tree_item[path_key]
            
            # Only update if selection is different
            current_selection = self.folder_tree.selection()
            if not current_selection or current_selection[0] != tree_item:
                # Set flag to prevent on_folder_select from triggering navigation
                self._updating_tree_selection = True
                self.folder_tree.selection_set(tree_item)
                self.folder_tree.see(tree_item)  # Scroll to make it visible
                self._updating_tree_selection = False
    
    def on_folder_select(self, event):
        """Handle folder selection in tree."""
        # Ignore if we're programmatically updating the selection
        if hasattr(self, '_updating_tree_selection') and self._updating_tree_selection:
            return
        
        selection = self.folder_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        folder_path = self.folder_tree.item(item)["values"]
        
        if not folder_path:
            return
        
        folder_path = Path(folder_path[0])
        
        # Find first image in this folder
        if folder_path in self.folder_structure and self.folder_structure[folder_path]:
            first_image = self.folder_structure[folder_path][0]
            if first_image in self.image_files:
                self.current_index = self.image_files.index(first_image)
                self.show_current_image()
    
    def on_images_loaded(self):
        """Called when image collection is complete."""
        try:
            debug_print("on_images_loaded called")
            self.loading = False
            
            if not self.image_files:
                debug_print("No images found")
                messagebox.showinfo("No Images", "No image files found in the directory.")
                self.window.destroy()
                return
            
            debug_print(f"Loading complete with {len(self.image_files)} images")
            self.window.title("Image Viewer")
            self.populate_tree()
            debug_print("Showing first image")
            self.show_current_image()
            debug_print("Image viewer ready")
        except Exception as e:
            debug_print(f"Error in on_images_loaded: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load images:\n{str(e)}\n\nCheck console for details.")
    
    def setup_ui(self):
        # Top info bar with fixed height
        info_frame = tk.Frame(self.window, bg="#f0f0f0", padx=10, pady=5, height=40)
        info_frame.pack(fill=tk.X)
        info_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.filename_label = tk.Label(info_frame, text="", font=("Arial", 10, "bold"), bg="#f0f0f0")
        self.filename_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Sort dropdown
        tk.Label(info_frame, text="Sort by:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.RIGHT, padx=(10, 5))
        sort_options = ["Path", "Created (Newest)", "Created (Oldest)", "Modified (Newest)", "Modified (Oldest)"]
        sort_values = ["path", "created_desc", "created_asc", "modified_desc", "modified_asc"]
        
        sort_dropdown = tk.OptionMenu(info_frame, self.sort_method, *sort_values, command=self.on_sort_changed)
        sort_dropdown.config(font=("Arial", 9), bg="#ffffff", width=15)
        sort_dropdown.pack(side=tk.RIGHT, padx=5)
        
        # Update menu to show friendly names
        menu = sort_dropdown["menu"]
        menu.delete(0, "end")
        for option, value in zip(sort_options, sort_values):
            menu.add_command(label=option, command=lambda v=value: self.sort_method.set(v) or self.on_sort_changed(v))
        
        self.counter_label = tk.Label(info_frame, text="", font=("Arial", 9), bg="#f0f0f0")
        self.counter_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content area with tree and image
        content_frame = tk.Frame(self.window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Folder tree and jump controls
        tree_frame = tk.Frame(content_frame, bg="#ffffff", width=200)
        tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        tree_frame.pack_propagate(False)  # Keep fixed width
        
        # Jump to index controls at top
        jump_control_frame = tk.Frame(tree_frame, bg="#ffffff", pady=10)
        jump_control_frame.pack(fill=tk.X, padx=5)
        
        tk.Label(jump_control_frame, text="Jump to:", font=("Arial", 9, "bold"), bg="#ffffff").pack(anchor=tk.W)
        
        jump_input_frame = tk.Frame(jump_control_frame, bg="#ffffff")
        jump_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.jump_entry = tk.Entry(jump_input_frame, font=("Arial", 9), width=10)
        self.jump_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.jump_entry.bind('<Return>', lambda e: self.jump_to_index())
        
        jump_btn = tk.Button(jump_input_frame, text="Go", 
                            command=self.jump_to_index,
                            font=("Arial", 9),
                            width=4)
        jump_btn.pack(side=tk.RIGHT)
        
        # Separator
        tk.Frame(tree_frame, bg="#d0d0d0", height=1).pack(fill=tk.X, pady=10)
        
        # Folder tree
        tk.Label(tree_frame, text="Folders", font=("Arial", 10, "bold"), bg="#ffffff").pack(pady=5)
        
        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.folder_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, show="tree")
        self.folder_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.folder_tree.yview)
        
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_select)
        
        # Right panel - Image display area
        self.image_frame = tk.Frame(content_frame, bg="gray")
        self.image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(self.image_frame, bg="gray", width=1, height=1)
        self.image_label.pack(expand=True, fill=tk.BOTH)
        
        # Navigation and action buttons with fixed height
        nav_frame = tk.Frame(self.window, padx=10, pady=10, height=50)
        nav_frame.pack(fill=tk.X)
        nav_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.prev_btn = tk.Button(nav_frame, text="← Previous", 
                                  command=self.previous_image,
                                  font=("Arial", 10, "bold"),
                                  width=12, pady=5)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(nav_frame, text="Next →", 
                                  command=self.next_image,
                                  font=("Arial", 10, "bold"),
                                  width=12, pady=5)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        open_location_btn = tk.Button(nav_frame, text="Explorer", 
                                      command=self.open_in_explorer,
                                      font=("Arial", 9),
                                      width=10, pady=5)
        open_location_btn.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(open_location_btn, "Open file location in Windows Explorer")
        
        open_viewer_btn = tk.Button(nav_frame, text="Viewer", 
                                    command=self.open_in_viewer,
                                    font=("Arial", 9),
                                    width=10, pady=5)
        open_viewer_btn.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(open_viewer_btn, "Open in Windows default image viewer")
        
        open_paint_btn = tk.Button(nav_frame, text="Paint", 
                                   command=self.open_in_paint,
                                   font=("Arial", 9),
                                   width=10, pady=5)
        open_paint_btn.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(open_paint_btn, "Open in Microsoft Paint for editing")
        
        # Keyboard bindings
        self.window.bind("<Left>", lambda e: self.previous_image())
        self.window.bind("<Right>", lambda e: self.next_image())
        
        # Bind resize event to update image
        self.window.bind("<Configure>", self.on_window_resize)
        self.last_window_size = (self.window.winfo_width(), self.window.winfo_height())
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", 
                           relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
            label.pack()
            widget._tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                del widget._tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def on_window_resize(self, event):
        """Handle window resize to rescale image."""
        # Only update if the window size actually changed (not just move)
        current_size = (self.window.winfo_width(), self.window.winfo_height())
        if current_size != self.last_window_size:
            self.last_window_size = current_size
            # Delay the image update slightly to avoid too many updates during resize
            if hasattr(self, '_resize_timer'):
                self.window.after_cancel(self._resize_timer)
            self._resize_timer = self.window.after(100, self.show_current_image)
    
    def show_current_image(self):
        """Display the current image."""
        try:
            if not self.image_files or self.loading:
                debug_print(f"show_current_image skipped: files={len(self.image_files)}, loading={self.loading}")
                return
            
            image_path = self.image_files[self.current_index]
            debug_print(f"Showing image {self.current_index + 1}/{len(self.image_files)}: {image_path.name}")
            
            # Update filename and counter
            self.filename_label.config(text=image_path.name)
            self.counter_label.config(text=f"{self.current_index + 1} / {len(self.image_files)}")
            
            # Update folder tree selection
            self.update_tree_selection()
            
            # Update button states
            self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.current_index < len(self.image_files) - 1 else tk.DISABLED)
            
            # Load and display image
            img = Image.open(image_path)
            
            # Get actual frame dimensions
            self.window.update_idletasks()
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()
            
            # Use default size if frame not yet drawn
            if frame_width <= 1:
                frame_width = 780
            if frame_height <= 1:
                frame_height = 420
            
            # Calculate scaling to fill the frame while maintaining aspect ratio
            img_width, img_height = img.size
            scale = min(frame_width / img_width, frame_height / img_height)
            
            # Scale up or down to fill the frame better
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Use NEAREST for pixel art to keep sharp edges
            img_resized = img.resize((new_width, new_height), Image.Resampling.NEAREST)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img_resized)
            self.image_label.config(image=photo, text="", compound=tk.CENTER)
            self.image_label.image = photo  # Keep a reference
            debug_print("Image displayed successfully")
            
        except Exception as e:
            debug_print(f"Error loading image: {e}")
            traceback.print_exc()
            self.image_label.config(image="", text=f"Error loading image:\n{e}", 
                                   fg="red", font=("Arial", 10), compound=tk.CENTER)
    
    def previous_image(self):
        """Show previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
    
    def next_image(self):
        """Show next image."""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.show_current_image()
    
    def jump_to_index(self):
        """Jump to a specific index."""
        try:
            target = int(self.jump_entry.get())
            if 1 <= target <= len(self.image_files):
                self.current_index = target - 1  # Convert to 0-based index
                self.show_current_image()
                self.jump_entry.delete(0, tk.END)
            else:
                messagebox.showwarning("Invalid Index", f"Please enter a number between 1 and {len(self.image_files)}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number")
    
    def open_in_explorer(self):
        """Open Windows Explorer at the image location."""
        if not self.image_files:
            return
        
        image_path = self.image_files[self.current_index]
        
        # Open explorer and select the file
        subprocess.run(['explorer', '/select,', str(image_path.absolute())])
    
    def open_in_viewer(self):
        """Open image in Windows default image viewer."""
        if not self.image_files:
            return
        
        image_path = self.image_files[self.current_index]
        
        try:
            # Use os.startfile to open with default viewer
            os.startfile(str(image_path.absolute()))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image in viewer:\n{e}")
    
    def open_in_paint(self):
        """Open image in Microsoft Paint."""
        if not self.image_files:
            return
        
        image_path = self.image_files[self.current_index]
        
        try:
            # Open with mspaint.exe
            subprocess.run(['mspaint', str(image_path.absolute())])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image in Paint:\n{e}")
