#!/usr/bin/env python3
"""
About Dialog for WebP Converter
Displays application information, features, and version details
"""

import tkinter as tk
from tkinter import ttk
from lang_manager import get_about

class AboutDialog:
    """About dialog window for WebP Converter"""
    
    def __init__(self, parent):
        self.parent = parent
        self.create_dialog()
    
    def create_dialog(self):
        """Create and show the About dialog"""
        self.about_window = tk.Toplevel(self.parent)
        self.about_window.title(get_about("title", "About WebP Converter"))
        self.about_window.geometry("450x500")
        self.about_window.resizable(False, False)
        self.about_window.transient(self.parent)
        self.about_window.grab_set()
        
        # Center the about window
        self.about_window.update_idletasks()
        x = (self.about_window.winfo_screenwidth() // 2) - (225)
        y = (self.about_window.winfo_screenheight() // 2) - (250)
        self.about_window.geometry(f"450x220+{x}+{y}")
        
        self.setup_content()
        self.setup_bindings()
        
    def setup_content(self):
        """Set up the dialog content"""
        # Main frame
        main_frame = ttk.Frame(self.about_window, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # App icon/title
        title_label = ttk.Label(main_frame, text=get_about("app_name", "🖼️ WebP Converter"), 
                               font=("Arial", 16, "bold"),
                               foreground="#2E7D32")
        title_label.pack(pady=(0, 10))
        
        # Version
        version_label = ttk.Label(main_frame, text=get_about("version", "Version 1.2.0"), 
                                 font=("Arial", 10))
        version_label.pack()
        
        # Description
        desc_text = get_about("description", """A modern Windows application for converting 
JPG and HEIC images to efficient WebP format.""")
        desc_label = ttk.Label(main_frame, text=desc_text, 
                              font=("Arial", 9),
                              justify="center")
        desc_label.pack(pady=(10, 0))
        
        # # Features
        # features_frame = ttk.LabelFrame(main_frame, text=get_about("features_title", "Features"), padding="10")
        # features_frame.pack(fill="x", pady=(15, 0))
        
        # features = get_about("features", [
        #     "✓ JPG/JPEG and HEIC to WebP conversion",
        #     "✓ Drag & drop interface",
        #     "✓ Batch processing",
        #     "✓ Quality control (1-100)",
        #     "✓ Metadata preservation",
        #     "✓ Progress tracking"
        # ])
        
        # for feature in features:
        #     feature_label = ttk.Label(features_frame, text=feature, 
        #                              font=("Arial", 8))
        #     feature_label.pack(anchor="w")
        
        # Supported Formats
#         formats_frame = ttk.LabelFrame(main_frame, text=get_about("supported_title", "Supported Formats"), padding="10")
#         formats_frame.pack(fill="x", pady=(10, 0))
        
#         supported_formats = get_about("supported_formats", [
#             "• JPEG: jpg, jpeg, jpe, jfif",
#             "• HEIC: heic, heics, heif, heifs, hif",
#             "• PNG: png, apng (animated)",
#             "• GIF: gif (animated)",
#             "• BMP: bmp, dib",
#             "• TIFF: tiff, tif",
#             "• AVIF: avif, avifs",
#             "• TGA: tga, icb, vda, vst",
#             "• Other: ico, psd"
#         ])
        
#         for format_info in supported_formats:
#             format_label = ttk.Label(formats_frame, text=format_info, 
#                                    font=("Arial", 8))
#             format_label.pack(anchor="w")
        
#         # Benefits
#         benefits_text = get_about("benefits", """WebP provides 25-35% smaller files than JPG
# with better quality and universal browser support.""")
#         benefits_label = ttk.Label(main_frame, text=benefits_text,
#                                   font=("Arial", 8, "italic"),
#                                   foreground="#666666",
#                                   justify="center")
#         benefits_label.pack(pady=(10, 0))
        
        # Copyright
        copyright_label = ttk.Label(main_frame, 
                                   text=get_about("copyright", "© 2024 - Open Source (MIT License)"),
                                   font=("Arial", 8),
                                   foreground="#888888")
        copyright_label.pack(pady=(15, 0))
        
        # Close button
        self.close_button = ttk.Button(main_frame, text=get_about("close", "Close"), 
                                      command=self.close_dialog)
        self.close_button.pack(pady=(15, 0))
        
    def setup_bindings(self):
        """Set up keyboard bindings and focus"""
        # Focus the close button
        self.close_button.focus()
        
        # Bind Escape key to close
        self.about_window.bind('<Escape>', lambda e: self.close_dialog())
        
        # Bind Enter key to close button
        self.about_window.bind('<Return>', lambda e: self.close_dialog())
        
    def close_dialog(self):
        """Close the about dialog"""
        self.about_window.destroy()

def show_about(parent):
    """Convenience function to show the about dialog"""
    AboutDialog(parent)
