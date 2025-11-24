"""
Converter tab - 3D Render to 2D Skin conversion.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image
from ui.tabs.base_tab import BaseTab


class ConverterTab(BaseTab):
    """Tab for converting 3D renders to 2D skins."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_ui()
    
    def create_ui(self):
        """Create the converter tab UI."""
        self.debug_log("Creating converter tab...")
        
        # Main container with padding
        main_frame = tk.Frame(self.frame, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="3D Render → 2D Skin Converter",
                              font=("Segoe UI", 18, "bold"),
                              fg=self.colors['primary'],
                              bg=self.colors['bg'])
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(main_frame,
                                 text="Convert a 3D character render to a flat 2D Minecraft skin PNG",
                                 font=("Segoe UI", 10),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['bg'])
        subtitle_label.pack(pady=(0, 20))
        
        # Input section
        input_card = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        input_card.pack(fill=tk.X, pady=(0, 15))
        
        input_inner = tk.Frame(input_card, bg=self.colors['card'])
        input_inner.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(input_inner,
                text="📥 Input Render Image",
                font=("Segoe UI", 12, "bold"),
                fg=self.colors['text'],
                bg=self.colors['card']).pack(anchor=tk.W, pady=(0, 10))
        
        # File selection
        file_frame = tk.Frame(input_inner, bg=self.colors['card'])
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.converter_input_path = tk.StringVar()
        input_entry = tk.Entry(file_frame,
                              textvariable=self.converter_input_path,
                              font=("Segoe UI", 10),
                              width=50)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(file_frame,
                              text="Browse",
                              command=self.browse_converter_input,
                              font=("Segoe UI", 10),
                              bg=self.colors['primary'],
                              fg="white",
                              relief=tk.FLAT,
                              cursor="hand2",
                              padx=20,
                              pady=8)
        browse_btn.pack(side=tk.LEFT)
        self.add_button_hover(browse_btn, self.colors['primary_dark'])
        
        # Output section
        output_card = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        output_card.pack(fill=tk.X, pady=(0, 15))
        
        output_inner = tk.Frame(output_card, bg=self.colors['card'])
        output_inner.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(output_inner,
                text="💾 Output Location",
                font=("Segoe UI", 12, "bold"),
                fg=self.colors['text'],
                bg=self.colors['card']).pack(anchor=tk.W, pady=(0, 10))
        
        output_file_frame = tk.Frame(output_inner, bg=self.colors['card'])
        output_file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.converter_output_path = tk.StringVar(value=os.path.join(os.getcwd(), "converted_skin.png"))
        output_entry = tk.Entry(output_file_frame,
                               textvariable=self.converter_output_path,
                               font=("Segoe UI", 10),
                               width=50)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        save_btn = tk.Button(output_file_frame,
                            text="Save As",
                            command=self.browse_converter_output,
                            font=("Segoe UI", 10),
                            bg=self.colors['primary'],
                            fg="white",
                            relief=tk.FLAT,
                            cursor="hand2",
                            padx=20,
                            pady=8)
        save_btn.pack(side=tk.LEFT)
        self.add_button_hover(save_btn, self.colors['primary_dark'])
        
        # Convert button
        convert_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        convert_frame.pack(pady=20)
        
        self.convert_btn = tk.Button(convert_frame,
                                    text="🔄 Convert to Skin",
                                    command=self.convert_render_to_skin,
                                    font=("Segoe UI", 12, "bold"),
                                    bg=self.colors['success'],
                                    fg="white",
                                    relief=tk.FLAT,
                                    cursor="hand2",
                                    padx=40,
                                    pady=12)
        self.convert_btn.pack()
        self.add_button_hover(self.convert_btn, "#27ae60")
        
        # Info section
        info_card = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        info_card.pack(fill=tk.BOTH, expand=True)
        
        info_inner = tk.Frame(info_card, bg=self.colors['card'])
        info_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(info_inner,
                text="ℹ️ How It Works",
                font=("Segoe UI", 11, "bold"),
                fg=self.colors['text'],
                bg=self.colors['card']).pack(anchor=tk.W, pady=(0, 10))
        
        info_text = (
            "This tool attempts to convert a 3D rendered character image into a flat 2D Minecraft skin.\n\n"
            "⚠️ NOTE: This is an experimental feature with limitations:\n"
            "• Works best with front-facing renders\n"
            "• May not capture all details from complex renders\n"
            "• Lighting and shading are approximated\n"
            "• Hidden parts are estimated from visible colors\n\n"
            "💡 For best results:\n"
            "• Use high-resolution renders (at least 256x256)\n"
            "• Ensure the character is centered and front-facing\n"
            "• Avoid heavily shadowed or lit renders"
        )
        
        info_label = tk.Label(info_inner,
                            text=info_text,
                            font=("Segoe UI", 9),
                            fg=self.colors['text_secondary'],
                            bg=self.colors['card'],
                            justify=tk.LEFT,
                            wraplength=600)
        info_label.pack(anchor=tk.W)
    
    def browse_converter_input(self):
        """Browse for input render image."""
        file_path = filedialog.askopenfilename(
            title="Select 3D Render Image",
            initialdir=os.getcwd(),
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if file_path:
            self.converter_input_path.set(file_path)
    
    def browse_converter_output(self):
        """Browse for output skin save location."""
        file_path = filedialog.asksaveasfilename(
            title="Save Converted Skin As",
            initialdir=os.getcwd(),
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")]
        )
        if file_path:
            self.converter_output_path.set(file_path)
    
    def convert_render_to_skin(self):
        """Convert 3D render to 2D skin."""
        from utils.feature_extractors import convert_render_to_skin
        
        input_path = self.converter_input_path.get()
        output_path = self.converter_output_path.get()
        
        if not input_path:
            messagebox.showerror("Error", "Please select an input render image.")
            return
        
        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Input file does not exist.")
            return
        
        if not output_path:
            messagebox.showerror("Error", "Please specify an output location.")
            return
        
        try:
            self.convert_btn.config(state=tk.DISABLED, text="Converting...")
            self.root.update()
            
            # Load the render image and convert
            render_img = Image.open(input_path)
            skin = convert_render_to_skin(render_img)
            
            # Save the result
            skin.save(output_path)
            
            self.convert_btn.config(state=tk.NORMAL, text="🔄 Convert to Skin")
            
            messagebox.showinfo(
                "Success",
                f"Skin converted and saved to:\n{output_path}\n\n"
                "Note: This is a basic conversion. The result may need manual editing."
            )
            
            # Ask if user wants to open the result
            if messagebox.askyesno("Open Result", "Would you like to open the converted skin?"):
                import sys
                import subprocess
                try:
                    if sys.platform == 'win32':
                        os.startfile(output_path)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', output_path])
                    else:
                        subprocess.run(['xdg-open', output_path])
                except:
                    pass
        
        except Exception as e:
            self.convert_btn.config(state=tk.NORMAL, text="🔄 Convert to Skin")
            messagebox.showerror("Error", f"Conversion failed:\n{type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
