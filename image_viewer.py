"""
Image viewer window for browsing images in a directory.
"""

import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import threading
import subprocess
from PIL import Image, ImageTk


class ImageViewerWindow:
    def __init__(self, parent, directory):
        self.window = tk.Toplevel(parent)
        self.window.title("Image Viewer - Loading...")
        self.window.geometry("800x600")
        
        self.directory = directory
        self.image_files = []
        self.current_index = 0
        self.loading = True
        
        # Setup UI first
        self.setup_ui()
        
        # Show loading message
        self.image_label.config(text="Loading images...\nPlease wait...", 
                               fg="white", font=("Arial", 14, "bold"))
        
        # Collect images in background thread to avoid freezing
        thread = threading.Thread(target=self.collect_images_background, daemon=True)
        thread.start()
    
    def collect_images_background(self):
        """Collect all image files from directory recursively in background."""
        # Common image extensions, including files without extensions
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', ''}
        temp_files = []
        count = 0
        
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = Path(root) / file
                # Quick check: just verify extension, don't open every file
                if file_path.suffix.lower() in image_extensions:
                    temp_files.append(file_path)
                    count += 1
                    # Update progress every 100 files
                    if count % 100 == 0:
                        self.window.after(0, lambda c=count: self.update_loading_status(c))
        
        # Sort by path for consistent order
        temp_files.sort()
        self.image_files = temp_files
        
        # Notify completion on main thread
        self.window.after(0, self.on_images_loaded)
    
    def update_loading_status(self, count):
        """Update loading message with count."""
        self.image_label.config(text=f"Loading images...\nFound {count} images so far...")
    
    def on_images_loaded(self):
        """Called when image collection is complete."""
        self.loading = False
        
        if not self.image_files:
            messagebox.showinfo("No Images", "No image files found in the directory.")
            self.window.destroy()
            return
        
        self.window.title("Image Viewer")
        self.show_current_image()
    
    def setup_ui(self):
        # Top info bar with fixed height
        info_frame = tk.Frame(self.window, bg="#f0f0f0", padx=10, pady=5, height=40)
        info_frame.pack(fill=tk.X)
        info_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.filename_label = tk.Label(info_frame, text="", font=("Arial", 10, "bold"), bg="#f0f0f0")
        self.filename_label.pack(side=tk.LEFT)
        
        open_location_btn = tk.Button(info_frame, text="Open in Explorer", 
                                      command=self.open_in_explorer,
                                      font=("Arial", 9))
        open_location_btn.pack(side=tk.RIGHT, padx=5)
        
        self.counter_label = tk.Label(info_frame, text="", font=("Arial", 9), bg="#f0f0f0")
        self.counter_label.pack(side=tk.RIGHT, padx=10)
        
        # Image display area
        self.image_frame = tk.Frame(self.window, bg="gray")
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.image_label = tk.Label(self.image_frame, bg="gray", width=1, height=1)
        self.image_label.pack(expand=True, fill=tk.BOTH)
        
        # Navigation buttons with fixed height
        nav_frame = tk.Frame(self.window, padx=10, pady=10, height=50)
        nav_frame.pack(fill=tk.X)
        nav_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.prev_btn = tk.Button(nav_frame, text="← Previous", 
                                  command=self.previous_image,
                                  font=("Arial", 10, "bold"),
                                  width=15, pady=5)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(nav_frame, text="Next →", 
                                  command=self.next_image,
                                  font=("Arial", 10, "bold"),
                                  width=15, pady=5)
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        # Keyboard bindings
        self.window.bind("<Left>", lambda e: self.previous_image())
        self.window.bind("<Right>", lambda e: self.next_image())
        
        # Bind resize event to update image
        self.window.bind("<Configure>", self.on_window_resize)
        self.last_window_size = (self.window.winfo_width(), self.window.winfo_height())
    
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
        if not self.image_files or self.loading:
            return
        
        image_path = self.image_files[self.current_index]
        
        # Update filename and counter
        self.filename_label.config(text=image_path.name)
        self.counter_label.config(text=f"{self.current_index + 1} / {len(self.image_files)}")
        
        # Update button states
        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_index < len(self.image_files) - 1 else tk.DISABLED)
        
        try:
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
            
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img_resized)
            self.image_label.config(image=photo, text="", compound=tk.CENTER)
            self.image_label.image = photo  # Keep a reference
            
        except Exception as e:
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
    
    def open_in_explorer(self):
        """Open Windows Explorer at the image location."""
        if not self.image_files:
            return
        
        image_path = self.image_files[self.current_index]
        
        # Open explorer and select the file
        subprocess.run(['explorer', '/select,', str(image_path.absolute())])
