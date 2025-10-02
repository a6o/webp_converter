#!/usr/bin/env python3
"""
WebP Converter - Convert JPG and HEIC images to WebP format
A Windows GUI application for batch image conversion
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pathlib import Path
from PIL import Image
import pillow_heif
from tkinterdnd2 import DND_FILES, TkinterDnD
from about_dialog import show_about
from lang_manager import init_language, get_lang_manager, get_main, get_menu, get_message, get_dialog
from config_manager import config
import time

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

class WebPConverter:
    def __init__(self, root, language=None):
        self.root = root
        
        # Load saved language if not specified
        if language is None:
            language = config.load_language()
        
        self.lang_manager = init_language(language)
        self.root.title(get_main("app_title", "WebP Converter"))
        self.root.resizable(False, False)  # Make window non-resizable
        
        # Variables - load saved settings
        saved_quality = config.load_quality()
        saved_metadata = config.load_preserve_metadata()
        saved_output = config.load_output_folder()
        saved_method = config.load_method()
        saved_lossless = config.load_lossless()
        saved_output_format = config.load_output_format()
        saved_white_border = config.load_white_border()
        saved_jpeg_quality = config.load_jpeg_quality()
        
        self.selected_files = []
        self.output_folder = tk.StringVar(value=saved_output)
        self.quality = tk.IntVar(value=saved_quality)
        self.preserve_metadata = tk.BooleanVar(value=saved_metadata)
        self.compression_method = tk.IntVar(value=saved_method)
        self.lossless_compression = tk.BooleanVar(value=saved_lossless)
        self.output_format = tk.StringVar(value=saved_output_format)
        self.white_border = tk.BooleanVar(value=saved_white_border)
        self.jpeg_quality = tk.IntVar(value=saved_jpeg_quality)
        
        # Image sizing options
        saved_resize_mode = config.load_resize_mode()
        saved_long_edge = config.load_long_edge()
        self.resize_mode = tk.StringVar(value=saved_resize_mode)  # "same_size" or "long_edge"
        self.long_edge_size = tk.StringVar(value=str(saved_long_edge))
        
        # Same location option
        saved_same_location = config.load_same_location()
        self.same_location = tk.BooleanVar(value=saved_same_location)
        
        self.conversion_running = False
        self.conversion_cancelled = False  # Flag to track if conversion was cancelled
        self.source_folder = None  # Track source folder for preserving structure
        
        # Set fixed window size
        self.root.geometry("600x500")
        
        self.setup_ui()
        self.setup_menu()
        self.setup_drag_drop()
        
        # Save settings when window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        # title_label = ttk.Label(main_frame, text="WebP Image Converter", 
        #                        font=("Arial", 16, "bold"))
        # title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        self.file_frame = ttk.LabelFrame(main_frame, text=get_main("select_images_title", "Select Images"), padding="10")
        self.file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.file_frame.columnconfigure(0, weight=1)
        
        self.select_files_btn = ttk.Button(self.file_frame, text=get_main("select_files", "Select JPG/HEIC Files"), 
                  command=self.select_files)
        self.select_files_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.select_folder_btn = ttk.Button(self.file_frame, text=get_main("select_folder", "Select Folder"), 
                  command=self.select_folder)
        self.select_folder_btn.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Selected files listbox with drag-drop hint
        listbox_frame = ttk.Frame(self.file_frame)
        listbox_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        # Drag-drop hint label (shows when no files selected)
        self.drop_hint_label = ttk.Label(listbox_frame, 
                                        text=get_main("drag_hint", "📁 Drag and drop JPG/HEIC files here\nor use the buttons above"), 
                                        font=("Arial", 10),
                                        foreground="gray",
                                        anchor="center")
        
        self.files_listbox = tk.Listbox(listbox_frame, height=8)
        self.files_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.files_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Clear files button
        self.clear_files_btn = ttk.Button(self.file_frame, text=get_main("clear_files", "Clear Files"), 
                  command=self.clear_files)
        self.clear_files_btn.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Output settings section
        self.output_frame = ttk.LabelFrame(main_frame, text=get_main("output_settings_title", "Output Settings"), padding="10")
        self.output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.output_frame.columnconfigure(1, weight=1)
        
        # Output folder
        self.output_label = ttk.Label(self.output_frame, text=get_main("output_folder", "Output Folder:"))
        self.output_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.output_entry = ttk.Entry(self.output_frame, textvariable=self.output_folder)
        self.output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.browse_btn = ttk.Button(self.output_frame, text=get_main("browse", "Browse"), 
                  command=self.select_output_folder)
        self.browse_btn.grid(row=0, column=2)
        
        # Same location checkbox
        self.same_location_checkbox = ttk.Checkbutton(self.output_frame, 
                                                     text=get_main("same_location", "Save as same location"),
                                                     variable=self.same_location, 
                                                     command=self.on_same_location_changed)
        self.same_location_checkbox.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Progress section
        self.progress_frame = ttk.LabelFrame(main_frame, text=get_main("progress_title", "Progress"), padding="10")
        self.progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.status_label = ttk.Label(self.progress_frame, text=get_main("ready_status", "Ready to convert images"))
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Convert button frame to hold both convert and cancel buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Convert button
        self.convert_button = ttk.Button(button_frame, text=get_main("convert_button", "Convert to WebP"), 
                                        command=self.start_conversion)
        self.convert_button.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Cancel button (initially hidden)
        self.cancel_button = ttk.Button(button_frame, text=get_main("cancel_button", "Cancel"), 
                                       command=self.cancel_conversion)
        # Don't grid it initially - it will be shown during conversion
        
        # Set default output folder to current directory
        self.output_folder.set(os.getcwd())
        
        # Update convert button text based on output format
        self.update_convert_button_text()
        
        # Update output folder controls state based on same location setting
        self.update_output_folder_state()
        
        # Show/hide drag-drop hint based on file list
        self.update_drag_drop_hint()
        
    def setup_menu(self):
        """Set up the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=get_menu("file", "File"), menu=file_menu)
        file_menu.add_command(label=get_menu("file_select", "Select Files..."), command=self.select_files, accelerator="Ctrl+O")
        file_menu.add_command(label=get_menu("file_folder", "Select Folder..."), command=self.select_folder, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label=get_menu("file_clear", "Clear Files"), command=self.clear_files, accelerator="Ctrl+L")
        file_menu.add_separator()
        file_menu.add_command(label=get_menu("file_exit", "Exit"), command=self.root.quit, accelerator="Alt+F4")
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=get_menu("settings", "Settings"), menu=settings_menu)
        settings_menu.add_command(label=get_menu("settings_output", "Choose Output Folder..."), command=self.select_output_folder)
        settings_menu.add_command(label=get_menu("settings_conversion", "Conversion Settings..."), command=self.show_settings_dialog)
        settings_menu.add_separator()
        
        # Language submenu
        lang_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Language / 언어", menu=lang_menu)
        
        # Add language options
        lang_names = self.lang_manager.get_language_names()
        for lang_code, lang_name in lang_names.items():
            lang_menu.add_command(
                label=lang_name,
                command=lambda code=lang_code: self.switch_language(code)
            )
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=get_menu("help", "Help"), menu=help_menu)
        help_menu.add_command(label=get_menu("help_about", "About WebP Converter"), command=self.show_about_dialog)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.select_files())
        self.root.bind('<Control-O>', lambda e: self.select_folder())  # Shift+Ctrl+O
        self.root.bind('<Control-l>', lambda e: self.clear_files())
        
    def show_about_dialog(self):
        """Show the About dialog"""
        show_about(self.root)
    
    def show_settings_dialog(self):
        """Show the settings dialog"""
        self.create_settings_dialog()
    
    def create_settings_dialog(self):
        """Create and show the conversion settings dialog"""
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title(get_dialog("settings_title", "Conversion Settings"))
        dialog.geometry("450x800")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (800 // 2)
        dialog.geometry(f"450x800+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        
        
        
        # Output Format section
        format_frame = ttk.LabelFrame(main_frame, text=get_main("format_settings", "Output Format"), padding="15")
        format_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # WebP radio button
        webp_radio = ttk.Radiobutton(format_frame, 
                                    text=get_main("format_webp", "Save as WebP"),
                                    variable=self.output_format, 
                                    value="webp",
                                    command=self.on_format_changed)
        webp_radio.grid(row=0, column=0, sticky=tk.W)
        
        # WebP-specific settings frame (nested under WebP option)
        self.webp_settings_frame = ttk.LabelFrame(format_frame, text="WebP Settings", padding="10")
        self.webp_settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0), padx=(20, 0))
        format_frame.columnconfigure(0, weight=1)
        self.webp_settings_frame.columnconfigure(1, weight=1)
        
        # Move quality controls to WebP frame
        quality_label = ttk.Label(self.webp_settings_frame, text=get_main("quality", "Quality:"))
        quality_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        quality_scale_frame = ttk.Frame(self.webp_settings_frame)
        quality_scale_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        quality_scale_frame.columnconfigure(0, weight=1)
        
        quality_scale = ttk.Scale(quality_scale_frame, from_=1, to=100, 
                                 variable=self.quality, orient="horizontal")
        quality_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        quality_value_label = ttk.Label(quality_scale_frame, text=str(self.quality.get()), width=3)
        quality_value_label.grid(row=0, column=1)
        
        # Update function for quality
        def update_quality_display(value=None):
            quality_value = int(float(self.quality.get()))
            quality_value_label.config(text=str(quality_value))
            config.save_quality(quality_value)
        
        quality_scale.configure(command=update_quality_display)
        
        # Move method controls to WebP frame
        method_label = ttk.Label(self.webp_settings_frame, text=get_main("method", "Method:"))
        method_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        method_scale_frame = ttk.Frame(self.webp_settings_frame)
        method_scale_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 0))
        method_scale_frame.columnconfigure(0, weight=1)
        
        method_scale = ttk.Scale(method_scale_frame, from_=0, to=6, 
                               variable=self.compression_method, orient="horizontal")
        method_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        method_value_label = ttk.Label(method_scale_frame, text=str(self.compression_method.get()), width=3)
        method_value_label.grid(row=0, column=1)
        
        # Update function for method
        def update_method_display(value=None):
            method_value = int(float(self.compression_method.get()))
            method_value_label.config(text=str(method_value))
            config.save_method(method_value)
        
        method_scale.configure(command=update_method_display)
        
        # Move lossless checkbox to WebP frame
        lossless_checkbox = ttk.Checkbutton(self.webp_settings_frame, 
                                           text=get_main("lossless_compression", "Lossless compression"),
                                           variable=self.lossless_compression, 
                                           command=self.on_lossless_changed)
        lossless_checkbox.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Move metadata checkbox to WebP frame
        metadata_checkbox = ttk.Checkbutton(self.webp_settings_frame, 
                                           text=get_main("preserve_metadata", "Preserve metadata"),
                                           variable=self.preserve_metadata, 
                                           command=self.on_metadata_changed)
        metadata_checkbox.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # JPEG radio button
        jpeg_radio = ttk.Radiobutton(format_frame, 
                                    text=get_main("format_jpeg", "Save as JPEG"),
                                    variable=self.output_format, 
                                    value="jpeg",
                                    command=self.on_format_changed)
        jpeg_radio.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        # JPEG-specific settings frame (nested under JPEG option)
        self.jpeg_settings_frame = ttk.LabelFrame(format_frame, text="JPEG Settings", padding="10")
        self.jpeg_settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0), padx=(20, 0))
        format_frame.columnconfigure(0, weight=1)
        self.jpeg_settings_frame.columnconfigure(1, weight=1)
        
        # JPEG quality controls
        jpeg_quality_label = ttk.Label(self.jpeg_settings_frame, text=get_main("quality", "Quality:"))
        jpeg_quality_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        jpeg_quality_scale_frame = ttk.Frame(self.jpeg_settings_frame)
        jpeg_quality_scale_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        jpeg_quality_scale_frame.columnconfigure(0, weight=1)
        
        jpeg_quality_scale = ttk.Scale(jpeg_quality_scale_frame, from_=0, to=95, 
                                      variable=self.jpeg_quality, orient="horizontal")
        jpeg_quality_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        jpeg_quality_value_label = ttk.Label(jpeg_quality_scale_frame, text=str(self.jpeg_quality.get()), width=3)
        jpeg_quality_value_label.grid(row=0, column=1)
        
        # Update function for JPEG quality
        def update_jpeg_quality_display(value=None):
            jpeg_quality_value = int(float(self.jpeg_quality.get()))
            jpeg_quality_value_label.config(text=str(jpeg_quality_value))
            config.save_jpeg_quality(jpeg_quality_value)
        
        jpeg_quality_scale.configure(command=update_jpeg_quality_display)
        
        # Format description
        format_desc = ttk.Label(format_frame,
                               text=get_dialog("format_desc", "WebP: Smaller files, better compression. JPEG: Universal compatibility."),
                               font=("TkDefaultFont", 8),
                               foreground="gray")
        format_desc.grid(row=4, column=0, sticky=tk.W, pady=(10, 0))
        
        # White Border section
        border_frame = ttk.LabelFrame(main_frame, text=get_main("border_settings", "Border Settings"), padding="15")
        border_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # White border checkbox
        border_checkbox = ttk.Checkbutton(border_frame, 
                                         text=get_main("white_border", "Add white border"),
                                         variable=self.white_border, 
                                         command=self.on_border_changed)
        border_checkbox.grid(row=0, column=0, sticky=tk.W)
        
        # Border description
        border_desc = ttk.Label(border_frame,
                               text=get_dialog("border_desc", "Creates 1440x1440 square with white border (long side = 1200px)"),
                               font=("TkDefaultFont", 8),
                               foreground="gray")
        border_desc.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Image Sizing section
        sizing_frame = ttk.LabelFrame(main_frame, text=get_main("sizing_settings", "Image Sizing"), padding="15")
        sizing_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Same size radio button
        self.same_size_radio = ttk.Radiobutton(sizing_frame, 
                                         text=get_main("same_size", "Keep original size"),
                                         variable=self.resize_mode, 
                                         value="same_size",
                                         command=self.on_resize_mode_changed)
        self.same_size_radio.grid(row=0, column=0, sticky=tk.W)
        
        # Long edge radio button with text input
        self.long_edge_frame = ttk.Frame(sizing_frame)
        self.long_edge_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        sizing_frame.columnconfigure(0, weight=1)
        
        self.long_edge_radio = ttk.Radiobutton(self.long_edge_frame, 
                                         text=get_main("set_long_edge", "Set long edge to:"),
                                         variable=self.resize_mode, 
                                         value="long_edge",
                                         command=self.on_resize_mode_changed)
        self.long_edge_radio.grid(row=0, column=0, sticky=tk.W)
        
        # Text input for long edge size
        self.long_edge_entry = ttk.Entry(self.long_edge_frame, 
                                        textvariable=self.long_edge_size,
                                        width=8)
        self.long_edge_entry.grid(row=0, column=1, padx=(10, 5), sticky=tk.W)
        self.long_edge_entry.bind('<KeyRelease>', self.on_long_edge_changed)
        
        # "px" label
        self.px_label = ttk.Label(self.long_edge_frame, text="px")
        self.px_label.grid(row=0, column=2, sticky=tk.W)
        
        # Sizing description
        self.sizing_desc = ttk.Label(sizing_frame,
                               text=get_dialog("sizing_desc", "Resize images while maintaining aspect ratio"),
                               font=("TkDefaultFont", 8),
                               foreground="gray")
        self.sizing_desc.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # Store reference to sizing frame for enable/disable functionality
        self.sizing_frame = sizing_frame
        
        # Footer section with informational text
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(20, 10))
        footer_frame.columnconfigure(0, weight=1)
        
        # Add a separator line
        separator = ttk.Separator(footer_frame, orient='horizontal')
        separator.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Footer text using ttk Label for consistency
        footer_content = get_dialog("settings_footer", 
            "Some settings may not work with large images. Try using higher method or lower quality.")
        
        footer_label = ttk.Label(footer_frame,
                                text=footer_content,
                                font=("TkDefaultFont", 8),
                                foreground="gray",
                                wraplength=400,  # Wrap text at 400 pixels
                                justify="left")
        footer_label.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Reset to defaults button
        reset_btn = ttk.Button(button_frame, text=get_dialog("reset_defaults", "Reset to Defaults"), 
                              command=lambda: self.reset_to_defaults(dialog, quality_scale, quality_value_label, 
                                                                    method_scale, method_value_label, 
                                                                    lossless_checkbox, metadata_checkbox, 
                                                                    webp_radio, jpeg_radio, border_checkbox))
        reset_btn.grid(row=0, column=0, padx=(0, 5), pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Close button
        close_btn = ttk.Button(button_frame, text=get_dialog("close", "Close"), 
                              command=dialog.destroy)
        close_btn.grid(row=0, column=1, padx=(5, 0), pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Initialize WebP settings state based on current selection
        self.update_webp_settings_state()
        
        # Initialize sizing settings state based on white border setting
        self.update_sizing_settings_state()
        
        # Focus the dialog
        dialog.focus_set()
    
    def switch_language(self, lang_code):
        """Switch application language dynamically"""
        if self.lang_manager.switch_language(lang_code):
            # Save language preference
            config.save_language(lang_code)
            
            # Update all UI elements with new language
            self.update_ui_language()
            
            # Show confirmation message
            # messagebox.showinfo(
            #     get_message("language_changed", "Language Changed"),
            #     get_message("language_applied", "Language has been applied successfully!")
            # )
    
    def update_ui_language(self):
        """Update all UI elements with current language"""
        # Update window title
        self.root.title(get_main("app_title", "WebP Converter"))
        
        # Update main UI elements (we'll need to store references to update them)
        if hasattr(self, 'select_files_btn'):
            self.select_files_btn.config(text=get_main("select_files", "Select JPG/HEIC Files"))
        if hasattr(self, 'select_folder_btn'):
            self.select_folder_btn.config(text=get_main("select_folder", "Select Folder"))
        if hasattr(self, 'clear_files_btn'):
            self.clear_files_btn.config(text=get_main("clear_files", "Clear Files"))
        if hasattr(self, 'output_label'):
            self.output_label.config(text=get_main("output_folder", "Output Folder:"))
        if hasattr(self, 'browse_btn'):
            self.browse_btn.config(text=get_main("browse", "Browse"))
        if hasattr(self, 'same_location_checkbox'):
            self.same_location_checkbox.config(text=get_main("same_location", "Save as same location"))
        if hasattr(self, 'convert_button'):
            # Update convert button text based on Instagram mode
            self.update_convert_button_text()
        if hasattr(self, 'status_label'):
            self.status_label.config(text=get_main("ready_status", "Ready to convert images"))
        if hasattr(self, 'progress_frame'):
            # Update progress frame label
            self.progress_frame.config(text=get_main("progress_title", "Progress"))
        
        # Update drag-drop hint
        if hasattr(self, 'drop_hint_label'):
            self.drop_hint_label.config(text=get_main("drag_hint", "📁 Drag and drop JPG/HEIC files here\nor use the buttons above"))
        
        # Update frame titles
        if hasattr(self, 'file_frame'):
            self.file_frame.config(text=get_main("select_images_title", "Select Images"))
        if hasattr(self, 'output_frame'):
            self.output_frame.config(text=get_main("output_settings_title", "Output Settings"))
        
        # Recreate the menu to update all menu items
        self.setup_menu()
        
    def setup_drag_drop(self):
        """Set up drag and drop functionality"""
        # Enable drag and drop on the files listbox
        self.files_listbox.drop_target_register(DND_FILES)
        self.files_listbox.dnd_bind('<<Drop>>', self.on_drop)
        
        # Also enable on the hint label
        self.drop_hint_label.drop_target_register(DND_FILES)
        self.drop_hint_label.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drop(self, event):
        """Handle dropped files"""
        if self.conversion_running:
            messagebox.showinfo(get_message("conversion_running", "Conversion Running"), 
                               get_message("conversion_wait", "Please wait for the current conversion to finish."))
            return
            
        # Get dropped files
        files = self.root.tk.splitlist(event.data)
        added_files = []
        
        for file_path in files:
            if os.path.isfile(file_path):
                # Check if it's a supported image file
                if self.is_supported_image(file_path):
                    if file_path not in self.selected_files:
                        # Clear source folder when dropping individual files
                        if not self.source_folder:
                            self.source_folder = None
                        self.selected_files.append(file_path)
                        added_files.append(os.path.basename(file_path))
            elif os.path.isdir(file_path):
                # If it's a directory, add all supported images and preserve structure
                new_files = self.get_images_from_folder(file_path)
                if new_files:
                    # Set source folder for structure preservation
                    self.source_folder = file_path
                    for new_file in new_files:
                        if new_file not in self.selected_files:
                            self.selected_files.append(new_file)
                            added_files.append(os.path.basename(new_file))
        
        if added_files:
            self.update_files_listbox()
        else:
            messagebox.showwarning(get_message("no_supported", "No Supported Files"), 
                                 get_message("no_supported_text", "No supported image files (JPG, JPEG, HEIC) were found in the dropped items."))
    
    def is_supported_image(self, file_path):
        """Check if file is a supported image format"""
        supported_extensions = {
            # JPEG formats
            '.jpg', '.jpeg', '.jpe', '.jfif',
            '.JPG', '.JPEG', '.JPE', '.JFIF',
            # HEIC formats  
            '.heic', '.heics', '.heif', '.heifs', '.hif',
            '.HEIC', '.HEICS', '.HEIF', '.HEIFS', '.HIF',
            # PNG formats
            '.png', '.apng', '.PNG', '.APNG',
            # GIF format
            '.gif', '.GIF',
            # BMP formats
            '.bmp', '.dib', '.BMP', '.DIB',
            # TIFF formats
            '.tiff', '.tif', '.TIFF', '.TIF',
            # AVIF formats
            '.avif', '.avifs', '.AVIF', '.AVIFS',
            # TGA formats
            '.tga', '.icb', '.vda', '.vst',
            '.TGA', '.ICB', '.VDA', '.VST',
            # Other common formats
            '.ico', '.ICO',
            '.psd', '.PSD'
        }
        return Path(file_path).suffix in supported_extensions
    
    def get_images_from_folder(self, folder_path):
        """Get all supported images from a folder"""
        folder_path = Path(folder_path)
        
        image_files = []
        for file in folder_path.rglob('*'):
            if file.is_file() and self.is_supported_image(file):
                image_files.append(str(file))
                
        return image_files
    
    def update_drag_drop_hint(self):
        """Show or hide the drag-drop hint based on whether files are selected"""
        if self.selected_files:
            self.drop_hint_label.grid_remove()
        else:
            self.drop_hint_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def update_quality_label(self, value=None):
        """Update the quality value label when scale changes"""
        quality_value = int(float(self.quality.get()))
        self.quality_value_label.config(text=str(quality_value))
        # Save quality setting
        config.save_quality(quality_value)
    
    def on_metadata_changed(self):
        """Handle metadata checkbox changes"""
        # Save metadata preference
        config.save_preserve_metadata(self.preserve_metadata.get())
    
    def on_lossless_changed(self):
        """Handle lossless compression checkbox changes"""
        # Save lossless preference
        config.save_lossless(self.lossless_compression.get())
    
    def on_format_changed(self):
        """Handle output format radio button changes"""
        # Save output format preference
        config.save_output_format(self.output_format.get())
        # Update convert button text to reflect output format
        self.update_convert_button_text()
        # Enable/disable WebP-specific settings
        self.update_webp_settings_state()
    
    def on_border_changed(self):
        """Handle white border checkbox changes"""
        # Save white border preference
        config.save_white_border(self.white_border.get())
        # Update sizing settings state based on border setting
        self.update_sizing_settings_state()
    
    def on_resize_mode_changed(self):
        """Handle resize mode radio button changes"""
        # Save resize mode preference
        config.save_resize_mode(self.resize_mode.get())
    
    def on_long_edge_changed(self, event=None):
        """Handle long edge size text input changes"""
        try:
            # Validate input is a positive integer
            size_str = self.long_edge_size.get().strip()
            if size_str and size_str.isdigit():
                size = int(size_str)
                if size > 0:
                    config.save_long_edge(size)
        except (ValueError, AttributeError):
            # Invalid input, don't save
            pass
    
    def on_same_location_changed(self):
        """Handle same location checkbox changes"""
        # Save same location preference
        config.save_same_location(self.same_location.get())
        # Update output folder controls state
        self.update_output_folder_state()
    
    def update_output_folder_state(self):
        """Enable/disable output folder controls based on same location setting"""
        same_location_enabled = self.same_location.get()
        folder_controls_enabled = not same_location_enabled
        
        # Enable/disable output folder controls
        if hasattr(self, 'output_entry'):
            self.output_entry.config(state='normal' if folder_controls_enabled else 'disabled')
        if hasattr(self, 'browse_btn'):
            self.browse_btn.config(state='normal' if folder_controls_enabled else 'disabled')
        if hasattr(self, 'output_label'):
            # Change label color to indicate disabled state
            if folder_controls_enabled:
                self.output_label.config(foreground='black')
            else:
                self.output_label.config(foreground='gray')
    
    def apply_white_border(self, img):
        """Apply white border: resize to fit 1440x1440 with long side = 1200px"""
        # Target dimensions
        canvas_size = 1440
        max_image_size = 1200
        
        # Get current image dimensions
        original_width, original_height = img.size
        
        # Calculate scaling factor to make longest side = 1200
        if original_width >= original_height:
            # Width is longer or equal
            scale_factor = max_image_size / original_width
        else:
            # Height is longer
            scale_factor = max_image_size / original_height
        
        # Calculate new dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize the image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create white canvas
        canvas = Image.new('RGB', (canvas_size, canvas_size), 'white')
        
        # Calculate position to center the image
        x_offset = (canvas_size - new_width) // 2
        y_offset = (canvas_size - new_height) // 2
        
        # Paste the resized image onto the canvas
        if resized_img.mode == 'RGBA':
            # Handle transparency
            canvas.paste(resized_img, (x_offset, y_offset), resized_img)
        else:
            canvas.paste(resized_img, (x_offset, y_offset))
        
        return canvas
    
    def apply_resize(self, img):
        """Apply resize based on user settings"""
        if self.resize_mode.get() == "long_edge":
            try:
                target_size = int(self.long_edge_size.get())
                if target_size > 0:
                    # Get current dimensions
                    width, height = img.size
                    
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        # Landscape: width is the long edge
                        new_width = target_size
                        new_height = int(height * target_size / width)
                    else:
                        # Portrait or square: height is the long edge
                        new_height = target_size
                        new_width = int(width * target_size / height)
                    
                    # Resize the image
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except (ValueError, AttributeError):
                # Invalid size, keep original
                pass
        
        return img
    
    def get_unique_filename(self, file_path):
        """Generate a unique filename if the file already exists"""
        path = Path(file_path)
        
        if not path.exists():
            return file_path
        
        # File exists, generate unique name
        base_name = path.stem
        extension = path.suffix
        parent_dir = path.parent
        counter = 1
        
        while True:
            new_name = f"{base_name} ({counter}){extension}"
            new_path = parent_dir / new_name
            if not new_path.exists():
                return str(new_path)
            counter += 1
    
    def update_convert_button_text(self):
        """Update convert button text based on output format"""
        if self.output_format.get() == "jpeg":
            button_text = get_main("convert_button_jpg", "Convert to JPG")
        else:
            button_text = get_main("convert_button", "Convert to WebP")
        
        if hasattr(self, 'convert_button'):
            self.convert_button.config(text=button_text)
    
    def update_webp_settings_state(self):
        """Enable/disable format-specific settings based on output format"""
        output_format = self.output_format.get()
        is_webp = output_format == "webp"
        is_jpeg = output_format == "jpeg"
        
        # Helper function to update widget state
        def update_widget_state(widget, enabled):
            widget_class = widget.winfo_class()
            state = 'normal' if enabled else 'disabled'
            # Only apply state to widgets that support it
            if widget_class in ('TScale', 'TCheckbutton', 'Scale', 'Checkbutton'):
                try:
                    widget.config(state=state)
                except:
                    pass  # Some widgets might not support state
            elif widget_class in ('TLabel', 'Label'):
                # For labels, we can change the foreground color to simulate disabled state
                try:
                    if enabled:
                        widget.config(foreground='black')
                    else:
                        widget.config(foreground='gray')
                except:
                    pass
            
            # Handle nested widgets
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    update_widget_state(child, enabled)
        
        # Update WebP settings frame
        if hasattr(self, 'webp_settings_frame'):
            for child in self.webp_settings_frame.winfo_children():
                update_widget_state(child, is_webp)
        
        # Update JPEG settings frame
        if hasattr(self, 'jpeg_settings_frame'):
            for child in self.jpeg_settings_frame.winfo_children():
                update_widget_state(child, is_jpeg)
    
    def update_sizing_settings_state(self):
        """Enable/disable sizing settings based on white border setting"""
        # If white border is enabled, disable sizing settings since border has fixed sizing
        white_border_enabled = self.white_border.get()
        sizing_enabled = not white_border_enabled
        
        # Helper function to update widget state
        def update_widget_state(widget, enabled):
            widget_class = widget.winfo_class()
            state = 'normal' if enabled else 'disabled'
            # Only apply state to widgets that support it
            if widget_class in ('TScale', 'TCheckbutton', 'TRadiobutton', 'TEntry', 'Scale', 'Checkbutton', 'Radiobutton', 'Entry'):
                try:
                    widget.config(state=state)
                except:
                    pass  # Some widgets might not support state
            elif widget_class in ('TLabel', 'Label'):
                # For labels, change foreground color to simulate disabled state
                try:
                    if enabled:
                        widget.config(foreground='black')
                    else:
                        widget.config(foreground='gray')
                except:
                    pass
        
        # Update sizing frame widgets if they exist
        if hasattr(self, 'same_size_radio'):
            update_widget_state(self.same_size_radio, sizing_enabled)
        if hasattr(self, 'long_edge_radio'):
            update_widget_state(self.long_edge_radio, sizing_enabled)
        if hasattr(self, 'long_edge_entry'):
            update_widget_state(self.long_edge_entry, sizing_enabled)
        if hasattr(self, 'px_label'):
            update_widget_state(self.px_label, sizing_enabled)
        if hasattr(self, 'sizing_desc'):
            update_widget_state(self.sizing_desc, sizing_enabled)
    
    def reset_to_defaults(self, dialog, quality_scale, quality_value_label, method_scale, method_value_label, lossless_checkbox, metadata_checkbox, webp_radio, jpeg_radio, border_checkbox):
        """Reset all settings to their default values"""
        import tkinter.messagebox as msgbox
        
        # Ask for confirmation
        if msgbox.askyesno(get_dialog("confirm_reset", "Confirm Reset"), 
                          get_dialog("confirm_reset_msg", "Reset all settings to default values?")):
            # Set default values
            default_quality = 80
            default_method = 0
            default_lossless = False
            default_metadata = True
            default_format = "webp"
            default_border = False
            default_jpeg_quality = 95
            default_resize_mode = "same_size"
            default_long_edge = 1920
            default_same_location = False
            
            # Update UI elements
            self.quality.set(default_quality)
            quality_value_label.config(text=str(default_quality))
            
            self.compression_method.set(default_method)
            method_value_label.config(text=str(default_method))
            
            self.lossless_compression.set(default_lossless)
            self.preserve_metadata.set(default_metadata)
            self.output_format.set(default_format)
            self.white_border.set(default_border)
            self.jpeg_quality.set(default_jpeg_quality)
            self.resize_mode.set(default_resize_mode)
            self.long_edge_size.set(str(default_long_edge))
            self.same_location.set(default_same_location)
            
            # Update convert button text and settings state
            self.update_convert_button_text()
            self.update_webp_settings_state()
            self.update_output_folder_state()
            
            # Save to config
            config.save_quality(default_quality)
            config.save_method(default_method)
            config.save_lossless(default_lossless)
            config.save_preserve_metadata(default_metadata)
            config.save_output_format(default_format)
            config.save_white_border(default_border)
            config.save_jpeg_quality(default_jpeg_quality)
            config.save_resize_mode(default_resize_mode)
            config.save_long_edge(default_long_edge)
            config.save_same_location(default_same_location)
            
            # Show success message
            msgbox.showinfo(get_dialog("reset_success", "Settings Reset"), 
                           get_dialog("reset_success_msg", "All settings have been reset to default values."))
    
    def on_closing(self):
        """Handle application closing - save settings"""
        # Save current output folder if changed
        config.save_output_folder(self.output_folder.get())
        
        # Close the application
        self.root.destroy()
        
    def select_files(self):
        """Select individual files"""
        filetypes = get_dialog("file_types", [
            ("Image files", "*.jpg *.jpeg *.jpe *.jfif *.heic *.heics *.heif *.heifs *.hif *.png *.apng *.gif *.bmp *.dib *.tiff *.tif *.avif *.avifs *.tga *.icb *.vda *.vst *.ico *.psd"),
            ("JPEG files", "*.jpg *.jpeg *.jpe *.jfif"),
            ("HEIC files", "*.heic *.heics *.heif *.heifs *.hif"),
            ("PNG files", "*.png *.apng"),
            ("GIF files", "*.gif"),
            ("BMP files", "*.bmp *.dib"),
            ("TIFF files", "*.tiff *.tif"),
            ("AVIF files", "*.avif *.avifs"),
            ("TGA files", "*.tga *.icb *.vda *.vst"),
            ("Other formats", "*.ico *.psd"),
            ("All files", "*.*")
        ])
        
        files = filedialog.askopenfilenames(
            title=get_dialog("select_files_title", "Select Image Files"),
            filetypes=filetypes
        )
        
        if files:
            # Clear source folder when manually selecting files
            self.source_folder = None
            self.selected_files.extend(files)
            self.update_files_listbox()
            
    def select_folder(self):
        """Select a folder and add all supported images"""
        folder = filedialog.askdirectory(title=get_dialog("select_folder_title", "Select Folder with Images"))
        
        if folder:
            new_files = self.get_images_from_folder(folder)
                
            if new_files:
                # Store the source folder for preserving structure
                self.source_folder = folder
                self.selected_files.extend(new_files)
                self.update_files_listbox()
            else:
                messagebox.showinfo(get_message("no_images_found", "No Images Found"), 
                                   get_message("no_images_text", "No supported image files found in the selected folder."))
                
    def clear_files(self):
        """Clear the selected files list"""
        self.selected_files.clear()
        self.source_folder = None  # Clear source folder reference
        self.update_files_listbox()
        
    def update_files_listbox(self):
        """Update the files listbox display"""
        self.files_listbox.delete(0, tk.END)
        
        for file_path in self.selected_files:
            if self.source_folder:
                # Show relative path from source folder
                try:
                    source_path = Path(self.source_folder)
                    input_path = Path(file_path)
                    relative_path = input_path.relative_to(source_path)
                    display_name = str(relative_path)
                except ValueError:
                    # File is not within source folder, show just filename
                    display_name = os.path.basename(file_path)
            else:
                # No source folder, show just filename
                display_name = os.path.basename(file_path)
            
            self.files_listbox.insert(tk.END, display_name)
        
        # Update drag-drop hint visibility
        self.update_drag_drop_hint()
            
    def select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title=get_dialog("select_output_title", "Select Output Folder"))
        if folder:
            self.output_folder.set(folder)
            # Save the selected output folder
            config.save_output_folder(folder)
            
    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        if not self.selected_files:
            messagebox.showwarning(get_message("no_files", "No Files"), 
                                 get_message("no_files_text", "Please select some image files first."))
            return
            
        # Only check output folder if not using same location
        if not self.same_location.get() and not self.output_folder.get():
            messagebox.showwarning(get_message("no_output", "No Output Folder"), 
                                 get_message("no_output_text", "Please select an output folder."))
            return
            
        if self.conversion_running:
            messagebox.showinfo(get_message("conversion_running", "Conversion Running"), 
                              get_message("conversion_running_text", "A conversion is already in progress."))
            return
            
        # Start conversion in separate thread
        self.conversion_running = True
        
        thread = threading.Thread(target=self.convert_images)
        thread.daemon = True
        thread.start()
        
        # Show cancel button during conversion
        self.show_cancel_button()
        
    def cancel_conversion(self):
        """Cancel the ongoing conversion"""
        if self.conversion_running:
            self.conversion_cancelled = True
            self.root.after(0, self.update_status, get_main("cancelling_status", "Cancelling conversion..."))
        
    def show_cancel_button(self):
        """Show the cancel button and hide the convert button"""
        self.convert_button.grid_remove()
        self.cancel_button.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
    def hide_cancel_button(self):
        """Hide the cancel button and show the convert button"""
        self.cancel_button.grid_remove()
        self.convert_button.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
    def convert_images(self):
        """Convert images to WebP format"""
        try:

            start_time = time.time()
            total_files = len(self.selected_files)
            converted_count = 0
            failed_files = []
            
            for i, input_file in enumerate(self.selected_files):
                # Check if conversion was cancelled
                if self.conversion_cancelled:
                    break
                    
                try:
                    # Update status
                    filename = os.path.basename(input_file)
                    self.root.after(0, self.update_status, f"Converting: {filename}")
                    
                    # Convert image
                    self.convert_single_image(input_file)
                    converted_count += 1
                    
                except Exception as e:
                    failed_files.append(f"{os.path.basename(input_file)}: {str(e)}")
                    
                    
                # Update progress
                progress = ((i + 1) / total_files) * 100
                self.root.after(0, self.update_progress, progress)
                
            # Show completion message
            if self.conversion_cancelled:
                message = f"Conversion cancelled!\n\nConverted: {converted_count}/{total_files} files before cancellation"
            else:
                message = f"Conversion completed!\n\nConverted: {converted_count}/{total_files} files"
                
            if failed_files:
                message += f"\n\nFailed files:\n" + "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    message += f"\n... and {len(failed_files) - 5} more"

            
            message += f"\n\nTime taken: {time.time() - start_time:.1f} seconds"
            self.root.after(0, self.show_completion_message, message)
            
        except Exception as e:
            self.root.after(0, self.show_error_message, f"Conversion failed: {str(e)}")
            
        finally:
            self.conversion_running = False
            self.root.after(0, self.reset_ui)
            
    def convert_single_image(self, input_file):
        """Convert a single image file to WebP"""
        # Open image
        with Image.open(input_file) as img:
            # Convert to RGB if necessary (WebP doesn't support all modes)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Keep transparency for RGBA
                if img.mode == 'RGBA':
                    pass  # Keep as RGBA
                else:
                    img = img.convert('RGB')
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Apply resize if enabled (but not if white border is enabled, as it handles its own sizing)
            if not self.white_border.get():
                img = self.apply_resize(img)
            
            # Apply white border if enabled
            if self.white_border.get():
                img = self.apply_white_border(img)
                
            # Generate output path - preserve folder structure if source folder exists
            input_path = Path(input_file)
            
            # Determine output format and extension
            if self.output_format.get() == "jpeg":
                output_extension = '.jpg'
            else:
                output_extension = '.webp'
            
            # Determine output base directory
            if self.same_location.get():
                # Save in same location as source file
                output_base = input_path.parent
            else:
                # Use specified output folder
                output_base = Path(self.output_folder.get())
            
            if self.source_folder and not self.same_location.get():
                # Calculate relative path from source folder (only when not using same location)
                source_path = Path(self.source_folder)
                try:
                    relative_path = input_path.relative_to(source_path)
                    # Change extension
                    output_filename = relative_path.stem + output_extension
                    output_path = output_base / relative_path.parent / output_filename
                    
                    # Create subdirectories if they don't exist
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                except ValueError:
                    # File is not within source folder, use flat structure
                    output_filename = input_path.stem + output_extension
                    output_path = output_base / output_filename
            else:
                # Use flat structure (either no source folder or same location mode)
                output_filename = input_path.stem + output_extension
                output_path = output_base / output_filename
            
            # Generate unique filename if file already exists
            output_path = self.get_unique_filename(str(output_path))
            
            # Save with appropriate format
            if self.output_format.get() == "jpeg":
                # JPEG mode: Save with user-selected quality
                save_kwargs = {
                    'format': 'JPEG',
                    'quality': self.jpeg_quality.get(),  # User-selected JPEG quality
                    'optimize': True
                }
                # Ensure image is in RGB mode for JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
            else:
                # WebP mode: Save as WebP with user settings
                save_kwargs = {
                    'format': 'WebP',
                    'method': self.compression_method.get()  # User-selected compression method
                }
                
                # Add lossless or quality setting
                if self.lossless_compression.get():
                    save_kwargs['lossless'] = True
                else:
                    save_kwargs['quality'] = self.quality.get()
            
            if self.preserve_metadata.get():
                # Preserve EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    save_kwargs['exif'] = img.info.get('exif', b'')
                    
            img.save(output_path, **save_kwargs)
            
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_var.set(value)
        
    def show_completion_message(self, message):
        """Show completion message"""
        messagebox.showinfo(get_message("conversion_complete", "Conversion Complete"), message)
        
    def show_error_message(self, message):
        """Show error message"""
        messagebox.showerror(get_message("error", "Error"), message)
        
    def reset_ui(self):
        """Reset UI after conversion"""
        self.convert_button.config(state="normal")
        self.status_label.config(text="Ready to convert images")
        self.progress_var.set(0)
        self.conversion_cancelled = False  # Reset cancellation flag
        self.hide_cancel_button()  # Show convert button, hide cancel button

def main(language=None):
    """Main application entry point"""
    root = TkinterDnD.Tk()  # Use TkinterDnD root for drag-drop support
    app = WebPConverter(root, language)
    
    # Center the fixed-size window
    root.update_idletasks()
    width = 600
    height = 500
    
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
