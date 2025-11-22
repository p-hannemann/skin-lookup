import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading


def copy_and_rename_to_png(input_dir, log_callback=None):
    """
    Copy a directory recursively and add .png extension to all files in the output.
    
    Args:
        input_dir: Source directory path
        log_callback: Optional function to call with log messages
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    input_path = Path(input_dir)
    output_dir = f"{input_dir}_png"
    output_path = Path(output_dir)
    
    # Check if input directory exists
    if not input_path.exists():
        log(f"Error: Input directory '{input_dir}' does not exist.")
        return False
    
    if not input_path.is_dir():
        log(f"Error: '{input_dir}' is not a directory.")
        return False
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_count = 0
    # Walk through the input directory
    for root, dirs, files in os.walk(input_path):
        # Calculate relative path from input directory
        rel_path = Path(root).relative_to(input_path)
        current_output_dir = output_path / rel_path
        
        # Create subdirectories in output
        current_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy and rename files
        for file in files:
            src_file = Path(root) / file
            dst_file = current_output_dir / (file + '.png')
            
            try:
                shutil.copy2(src_file, dst_file)
                file_count += 1
                if file_count % 10 == 0:  # Log every 10 files to avoid spam
                    log(f"Copied {file_count} files...")
            except Exception as e:
                log(f"Error copying {src_file}: {e}")
    
    log(f"\nCompleted! {file_count} files copied from '{input_dir}' to '{output_dir}' with .png extension added.")
    return True


class SkinCopierGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Skin Copier - Add .png Extension")
        self.root.geometry("600x415")
        self.root.resizable(True, True)
        self.is_processing = False
        self.should_cancel = False
        self.current_output_dir = None
        
        # Input folder selection
        frame_input = tk.Frame(root, padx=10, pady=10)
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
        btn_frame = tk.Frame(root)
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
        
        # Log area
        log_frame = tk.Frame(root, padx=10, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(log_frame, text="Log:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  font=("Consolas", 9),
                                                  state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
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
    
    def browse_folder(self):
        initial_dir = os.getcwd()
        folder = filedialog.askdirectory(title="Select Input Folder", initialdir=initial_dir)
        if folder:
            self.folder_path.set(folder)
    
    def open_discord(self):
        import webbrowser
        # Try to copy username to clipboard
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("soulreturns")
            messagebox.showinfo("Discord", "Discord username 'soulreturns' copied to clipboard!")
        except:
            messagebox.showinfo("Discord", "Discord username: soulreturns")
    
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
            
            success = self.copy_with_cancel_check(folder)
            
            self.is_processing = False
            
            if self.should_cancel:
                # Clean up output directory
                self.log("\nCancelled - removing output directory...")
                try:
                    if os.path.exists(self.current_output_dir):
                        shutil.rmtree(self.current_output_dir)
                        self.log(f"Output directory '{self.current_output_dir}' removed.")
                    messagebox.showinfo("Cancelled", "Operation cancelled and output directory removed.")
                except Exception as e:
                    self.log(f"Error removing output directory: {e}")
                    messagebox.showerror("Error", f"Operation cancelled but failed to remove output directory:\n{e}")
            elif success:
                messagebox.showinfo("Success", f"Files copied successfully!\nOutput: {output_dir}")
            else:
                messagebox.showerror("Error", "Failed to copy files. Check the log for details.")
            
            self.process_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.current_output_dir = None
        
        # Run in separate thread to keep GUI responsive
        thread = threading.Thread(target=run_process, daemon=True)
        thread.start()
    
    def copy_with_cancel_check(self, input_dir):
        """Modified copy function that checks for cancellation."""
        input_path = Path(input_dir)
        output_dir = f"{input_dir}_png"
        output_path = Path(output_dir)
        merge_mode = self.merge_files.get()
        
        # Check if input directory exists
        if not input_path.exists():
            self.log(f"Error: Input directory '{input_dir}' does not exist.")
            return False
        
        if not input_path.is_dir():
            self.log(f"Error: '{input_dir}' is not a directory.")
            return False
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        if merge_mode:
            self.log("Merge mode: All files will be copied to a single folder.\n")
        
        file_count = 0
        file_name_counter = {}  # Track duplicate filenames when merging
        
        # Walk through the input directory
        for root, dirs, files in os.walk(input_path):
            # Check for cancellation
            if self.should_cancel:
                return False
            
            if merge_mode:
                # Merge mode: all files go to root output directory
                current_output_dir = output_path
            else:
                # Normal mode: preserve directory structure
                rel_path = Path(root).relative_to(input_path)
                current_output_dir = output_path / rel_path
                # Create subdirectories in output
                current_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy and rename files
            for file in files:
                # Check for cancellation before each file
                if self.should_cancel:
                    return False
                
                src_file = Path(root) / file
                
                if merge_mode:
                    # Handle potential duplicate filenames
                    base_name = file
                    if base_name in file_name_counter:
                        file_name_counter[base_name] += 1
                        # Add counter before .png extension
                        dst_file = current_output_dir / f"{base_name}_{file_name_counter[base_name]}.png"
                    else:
                        file_name_counter[base_name] = 0
                        dst_file = current_output_dir / (base_name + '.png')
                else:
                    dst_file = current_output_dir / (file + '.png')
                
                try:
                    shutil.copy2(src_file, dst_file)
                    file_count += 1
                    if file_count % 10 == 0:  # Log every 10 files to avoid spam
                        self.log(f"Copied {file_count} files...")
                except Exception as e:
                    self.log(f"Error copying {src_file}: {e}")
        
        if not self.should_cancel:
            mode_text = " (merged)" if merge_mode else ""
            self.log(f"\nCompleted! {file_count} files copied{mode_text} from '{input_dir}' to '{output_dir}' with .png extension added.")
        return True


if __name__ == "__main__":
    import sys
    
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        # Command line mode
        if len(sys.argv) != 2:
            print("Usage: python copy_skins.py <input_directory>")
            print("Example: python copy_skins.py skins")
            sys.exit(1)
        
        input_directory = sys.argv[1]
        copy_and_rename_to_png(input_directory)
    else:
        # GUI mode
        root = tk.Tk()
        app = SkinCopierGUI(root)
        root.mainloop()
