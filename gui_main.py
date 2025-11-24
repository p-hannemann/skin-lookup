"""
Main GUI application for Skin Copier with integrated skin matching.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
from pathlib import Path
import subprocess
from PIL import Image, ImageTk

from file_utils import copy_and_rename_to_png
from skin_matcher import find_matching_skins, copy_skin_files
from image_viewer import ImageViewerWindow


class SkinCopierGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Skin Copier & Matcher")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        self.is_processing = False
        self.should_cancel = False
        self.current_output_dir = None
        self.last_output_dir = None
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_matcher_tab()
        self.create_copier_tab()
        
        # Footer with credits
        footer_frame = tk.Frame(root, padx=10, pady=5)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        credits_label = tk.Label(footer_frame, 
                                text="☕ Made by SoulReturns", 
                                font=("Arial", 9),
                                fg="gray")
        credits_label.pack(side=tk.LEFT)
        
        discord_label = tk.Label(footer_frame, 
                                text="Discord: soulreturns", 
                                font=("Arial", 9),
                                fg="#5865F2",
                                cursor="hand2")
        discord_label.pack(side=tk.RIGHT)
        discord_label.bind("<Button-1>", lambda e: self.open_discord())
    
    def create_matcher_tab(self):
        """Create the skin matcher tab."""
        matcher_frame = tk.Frame(self.notebook)
        self.notebook.add(matcher_frame, text="Skin Matcher")
        
        # Input image selection
        frame_input = tk.Frame(matcher_frame, padx=10, pady=10)
        frame_input.pack(fill=tk.X)
        
        tk.Label(frame_input, text="Input Image (to match):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        img_frame = tk.Frame(frame_input)
        img_frame.pack(fill=tk.X, pady=5)
        
        self.input_image_path = tk.StringVar()
        entry = tk.Entry(img_frame, textvariable=self.input_image_path, font=("Arial", 10))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_img_btn = tk.Button(img_frame, text="Browse", command=self.browse_input_image, width=10)
        browse_img_btn.pack(side=tk.RIGHT)
        
        # Search directory selection
        tk.Label(frame_input, text="Search Directory (skins folder):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        dir_frame = tk.Frame(frame_input)
        dir_frame.pack(fill=tk.X, pady=5)
        
        self.search_dir_path = tk.StringVar()
        entry2 = tk.Entry(dir_frame, textvariable=self.search_dir_path, font=("Arial", 10))
        entry2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_dir_btn = tk.Button(dir_frame, text="Browse", command=self.browse_search_directory, width=10)
        browse_dir_btn.pack(side=tk.RIGHT)
        
        # Number of matches
        match_frame = tk.Frame(frame_input)
        match_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(match_frame, text="Top matches to find:", font=("Arial", 9)).pack(side=tk.LEFT)
        self.top_n_matches = tk.IntVar(value=5)
        spinner = tk.Spinbox(match_frame, from_=1, to=20, textvariable=self.top_n_matches, width=5, font=("Arial", 9))
        spinner.pack(side=tk.LEFT, padx=5)
        
        # Buttons frame
        btn_frame = tk.Frame(matcher_frame)
        btn_frame.pack(pady=10)
        
        self.match_btn = tk.Button(btn_frame, text="Find Matching Skins", 
                                   command=self.find_matches,
                                   font=("Arial", 11, "bold"),
                                   bg="#4CAF50", fg="white",
                                   padx=20, pady=10)
        self.match_btn.pack(side=tk.LEFT, padx=5)
        
        self.match_cancel_btn = tk.Button(btn_frame, text="Cancel", 
                                         command=self.cancel_matching,
                                         font=("Arial", 11, "bold"),
                                         bg="#f44336", fg="white",
                                         padx=20, pady=10,
                                         state=tk.DISABLED)
        self.match_cancel_btn.pack(side=tk.LEFT, padx=5)
        
        self.view_matches_btn = tk.Button(btn_frame, text="View Matches", 
                                         command=self.view_match_results,
                                         font=("Arial", 11, "bold"),
                                         bg="#2196F3", fg="white",
                                         padx=20, pady=10,
                                         state=tk.DISABLED)
        self.view_matches_btn.pack(side=tk.LEFT, padx=5)
        
        # Log area
        log_frame = tk.Frame(matcher_frame, padx=10, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(log_frame, text="Log:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.matcher_log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                          font=("Consolas", 9),
                                                          state=tk.DISABLED)
        self.matcher_log_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def create_copier_tab(self):
        """Create the file copier tab."""
        copier_frame = tk.Frame(self.notebook)
        self.notebook.add(copier_frame, text="File Copier")
        
        # Input folder selection
        frame_input = tk.Frame(copier_frame, padx=10, pady=10)
        frame_input.pack(fill=tk.X)
        
        tk.Label(frame_input, text="Input Folder:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        folder_frame = tk.Frame(frame_input)
        folder_frame.pack(fill=tk.X, pady=5)
        
        self.folder_path = tk.StringVar()
        entry = tk.Entry(folder_frame, textvariable=self.folder_path, font=("Arial", 10))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = tk.Button(folder_frame, text="Browse", command=self.browse_folder, width=10)
        browse_btn.pack(side=tk.RIGHT)
        
        # Info label
        info_label = tk.Label(frame_input, text="Output will be created as: [input_folder]_png", 
                             fg="gray", font=("Arial", 9))
        info_label.pack(anchor=tk.W)
        
        # Merge files toggle
        self.merge_files = tk.BooleanVar(value=False)
        merge_check = tk.Checkbutton(frame_input, 
                                     text="Merge all files into single folder (no subdirectories)",
                                     variable=self.merge_files,
                                     font=("Arial", 9))
        merge_check.pack(anchor=tk.W, pady=(5, 0))
        
        # Buttons frame
        btn_frame = tk.Frame(copier_frame)
        btn_frame.pack(pady=10)
        
        self.process_btn = tk.Button(btn_frame, text="Copy and Add .png Extension", 
                                     command=self.process_folder, 
                                     font=("Arial", 11, "bold"),
                                     bg="#4CAF50", fg="white",
                                     padx=20, pady=10)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = tk.Button(btn_frame, text="Cancel", 
                                    command=self.cancel_process, 
                                    font=("Arial", 11, "bold"),
                                    bg="#f44336", fg="white",
                                    padx=20, pady=10,
                                    state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        self.viewer_btn = tk.Button(btn_frame, text="View Images", 
                                    command=self.open_image_viewer, 
                                    font=("Arial", 11, "bold"),
                                    bg="#2196F3", fg="white",
                                    padx=20, pady=10)
        self.viewer_btn.pack(side=tk.LEFT, padx=5)
        
        # Check for existing output directory on startup
        self.check_for_existing_output()
        self.update_viewer_button_state()
        
        # Log area
        log_frame = tk.Frame(copier_frame, padx=10, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(log_frame, text="Log:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  font=("Consolas", 9),
                                                  state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
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
        initial_dir = os.getcwd()
        folder = filedialog.askdirectory(title="Select Search Directory", initialdir=initial_dir)
        if folder:
            self.search_dir_path.set(folder)
    
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
