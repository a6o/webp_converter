"""
Configuration Manager for WebP Converter
Saves settings to Windows Registry for true portability
"""

import winreg
import os
from pathlib import Path


class ConfigManager:
    """Manages application configuration using Windows Registry"""
    
    REGISTRY_PATH = r"Software\WebPConverter"
    
    def __init__(self):
        """Initialize the configuration manager"""
        pass  # No persistent registry key needed
    
    def save_setting(self, name, value):
        """Save a setting to the registry"""
        try:
            # Open/create key, set value, and close immediately
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH)
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(value))
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Warning: Could not save setting {name}: {e}")
            return False
    
    def load_setting(self, name, default_value=None):
        """Load a setting from the registry"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH)
            value, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return value
        except (FileNotFoundError, OSError):
            return default_value
    
    def save_int_setting(self, name, value):
        """Save an integer setting to the registry"""
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH)
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Warning: Could not save integer setting {name}: {e}")
            return False
    
    def load_int_setting(self, name, default_value=0):
        """Load an integer setting from the registry"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH)
            value, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return int(value)
        except (FileNotFoundError, OSError, ValueError):
            return default_value
    
    def save_bool_setting(self, name, value):
        """Save a boolean setting to the registry"""
        return self.save_int_setting(name, 1 if value else 0)
    
    def load_bool_setting(self, name, default_value=False):
        """Load a boolean setting from the registry"""
        return bool(self.load_int_setting(name, 1 if default_value else 0))
    
    def delete_setting(self, name):
        """Delete a setting from the registry"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            return True
        except (FileNotFoundError, OSError):
            return False
    
    def clear_all_settings(self):
        """Clear all application settings"""
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH)
            self._ensure_registry_key()
            return True
        except (FileNotFoundError, OSError):
            return False
    
    def get_all_settings(self):
        """Get all saved settings as a dictionary"""
        settings = {}
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    settings[name] = value
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except (FileNotFoundError, OSError):
            pass
        return settings
    
    def __del__(self):
        """Clean up registry key handle"""
        pass  # No persistent handles to clean up


# Application-specific configuration methods
class WebPConverterConfig(ConfigManager):
    """WebP Converter specific configuration manager"""
    
    def save_language(self, language_code):
        """Save the selected language"""
        return self.save_setting("Language", language_code)
    
    def load_language(self):
        """Load the selected language (default: English)"""
        return self.load_setting("Language", "en")
    
    def save_output_folder(self, folder_path):
        """Save the last used output folder"""
        return self.save_setting("OutputFolder", folder_path)
    
    def load_output_folder(self):
        """Load the last used output folder (default: current directory)"""
        default_path = os.getcwd()
        return self.load_setting("OutputFolder", default_path)
    
    def save_quality(self, quality):
        """Save the quality setting (1-100)"""
        return self.save_int_setting("Quality", quality)
    
    def load_quality(self):
        """Load the quality setting (default: 80)"""
        return self.load_int_setting("Quality", 80)
    
    def save_preserve_metadata(self, preserve):
        """Save the preserve metadata setting"""
        return self.save_bool_setting("PreserveMetadata", preserve)
    
    def load_preserve_metadata(self):
        """Load the preserve metadata setting (default: True)"""
        return self.load_bool_setting("PreserveMetadata", True)
    
    def save_window_geometry(self, geometry):
        """Save window size and position"""
        return self.save_setting("WindowGeometry", geometry)
    
    def load_window_geometry(self):
        """Load window size and position"""
        return self.load_setting("WindowGeometry", None)
    
    def save_last_files_folder(self, folder_path):
        """Save the last folder used for file selection"""
        return self.save_setting("LastFilesFolder", folder_path)
    
    def load_last_files_folder(self):
        """Load the last folder used for file selection"""
        return self.load_setting("LastFilesFolder", os.getcwd())
    
    def save_method(self, method):
        """Save WebP compression method (0-6)"""
        return self.save_int_setting("CompressionMethod", method)
    
    def load_method(self):
        """Load WebP compression method (0-6), default to 6 (best quality)"""
        return self.load_int_setting("CompressionMethod", 0)
    
    def save_lossless(self, lossless):
        """Save lossless compression setting"""
        return self.save_bool_setting("LosslessCompression", lossless)
    
    def load_lossless(self):
        """Load lossless compression setting, default to False (lossy)"""
        return self.load_bool_setting("LosslessCompression", False)
    
    def save_output_format(self, output_format):
        """Save output format setting (webp or jpeg)"""
        return self.save_setting("OutputFormat", output_format)
    
    def load_output_format(self):
        """Load output format setting, default to webp"""
        return self.load_setting("OutputFormat", "webp")
    
    def save_white_border(self, white_border):
        """Save white border setting"""
        return self.save_bool_setting("WhiteBorder", white_border)
    
    def load_white_border(self):
        """Load white border setting, default to False"""
        return self.load_bool_setting("WhiteBorder", False)
    
    def save_jpeg_quality(self, jpeg_quality):
        """Save JPEG quality setting"""
        return self.save_int_setting("JpegQuality", jpeg_quality)
    
    def load_jpeg_quality(self):
        """Load JPEG quality setting, default to 95"""
        return self.load_int_setting("JpegQuality", 95)
    
    def save_resize_mode(self, resize_mode):
        """Save resize mode setting"""
        return self.save_setting("ResizeMode", resize_mode)
    
    def load_resize_mode(self):
        """Load resize mode setting, default to 'same_size'"""
        return self.load_setting("ResizeMode", "same_size")
    
    def save_long_edge(self, long_edge):
        """Save long edge size setting"""
        return self.save_int_setting("LongEdge", long_edge)
    
    def load_long_edge(self):
        """Load long edge size setting, default to 1920"""
        return self.load_int_setting("LongEdge", 1920)
    
    def save_same_location(self, same_location):
        """Save same location setting"""
        return self.save_bool_setting("SameLocation", same_location)
    
    def load_same_location(self):
        """Load same location setting, default to False"""
        return self.load_bool_setting("SameLocation", False)


# Global instance for easy access
config = WebPConverterConfig()
