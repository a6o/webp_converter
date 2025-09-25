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
        
        self.selected_files = []
        self.output_folder = tk.StringVar(value=saved_output)
        self.quality = tk.IntVar(value=saved_quality)
        self.preserve_metadata = tk.BooleanVar(value=saved_metadata)
        self.conversion_running = False
        
        # Set fixed window size
        self.root.geometry("600x520")
        
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
        
        # Quality setting
        self.quality_title_label = ttk.Label(self.output_frame, text=get_main("quality", "Quality:"))
        self.quality_title_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        quality_frame = ttk.Frame(self.output_frame)
        quality_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.quality_scale = ttk.Scale(quality_frame, from_=1, to=100, 
                                      variable=self.quality, orient="horizontal")
        self.quality_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        quality_frame.columnconfigure(0, weight=1)
        
        self.quality_value_label = ttk.Label(quality_frame, text=str(self.quality.get()))
        self.quality_value_label.grid(row=0, column=1)
        
        self.quality_scale.configure(command=self.update_quality_label)
        
        # Preserve metadata checkbox
        self.metadata_checkbox = ttk.Checkbutton(self.output_frame, text=get_main("preserve_metadata", "Preserve metadata"), 
                       variable=self.preserve_metadata, command=self.on_metadata_changed)
        self.metadata_checkbox.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
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
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text=get_main("convert_button", "Convert to WebP"), 
                                        command=self.start_conversion)
        self.convert_button.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        # Set default output folder to current directory
        self.output_folder.set(os.getcwd())
        
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
        if hasattr(self, 'quality_title_label'):
            self.quality_title_label.config(text=get_main("quality", "Quality:"))
        if hasattr(self, 'metadata_checkbox'):
            self.metadata_checkbox.config(text=get_main("preserve_metadata", "Preserve metadata"))
        if hasattr(self, 'convert_button'):
            self.convert_button.config(text=get_main("convert_button", "Convert to WebP"))
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
                        self.selected_files.append(file_path)
                        added_files.append(os.path.basename(file_path))
            elif os.path.isdir(file_path):
                # If it's a directory, add all supported images
                new_files = self.get_images_from_folder(file_path)
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
            self.selected_files.extend(files)
            self.update_files_listbox()
            
    def select_folder(self):
        """Select a folder and add all supported images"""
        folder = filedialog.askdirectory(title=get_dialog("select_folder_title", "Select Folder with Images"))
        
        if folder:
            new_files = self.get_images_from_folder(folder)
                
            if new_files:
                self.selected_files.extend(new_files)
                self.update_files_listbox()
            else:
                messagebox.showinfo(get_message("no_images_found", "No Images Found"), 
                                   get_message("no_images_text", "No supported image files found in the selected folder."))
                
    def clear_files(self):
        """Clear the selected files list"""
        self.selected_files.clear()
        self.update_files_listbox()
        
    def update_files_listbox(self):
        """Update the files listbox display"""
        self.files_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            filename = os.path.basename(file_path)
            self.files_listbox.insert(tk.END, filename)
        
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
            
        if not self.output_folder.get():
            messagebox.showwarning(get_message("no_output", "No Output Folder"), 
                                 get_message("no_output_text", "Please select an output folder."))
            return
            
        if self.conversion_running:
            messagebox.showinfo(get_message("conversion_running", "Conversion Running"), 
                              get_message("conversion_running_text", "A conversion is already in progress."))
            return
            
        # Start conversion in separate thread
        self.conversion_running = True
        self.convert_button.config(state="disabled")
        
        thread = threading.Thread(target=self.convert_images)
        thread.daemon = True
        thread.start()
        
    def convert_images(self):
        """Convert images to WebP format"""
        try:
            total_files = len(self.selected_files)
            converted_count = 0
            failed_files = []
            
            for i, input_file in enumerate(self.selected_files):
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
            message = f"Conversion completed!\n\nConverted: {converted_count}/{total_files} files"
            if failed_files:
                message += f"\n\nFailed files:\n" + "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    message += f"\n... and {len(failed_files) - 5} more"
                    
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
                
            # Generate output filename
            input_path = Path(input_file)
            output_filename = input_path.stem + '.webp'
            output_path = Path(self.output_folder.get()) / output_filename
            
            # Save as WebP
            save_kwargs = {
                'format': 'WebP',
                'quality': self.quality.get(),
                'method': 6  # Better compression
            }
            
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

def main(language=None):
    """Main application entry point"""
    root = TkinterDnD.Tk()  # Use TkinterDnD root for drag-drop support
    app = WebPConverter(root, language)
    
    # Center the fixed-size window
    root.update_idletasks()
    width = 600
    height = 520
    
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
