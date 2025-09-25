#!/usr/bin/env python3
"""
Language Manager for WebP Converter
Handles internationalization and language switching
"""

import os
import sys
import json
from pathlib import Path

class LanguageManager:
    """Manages language loading and switching"""
    
    def __init__(self, default_lang='en'):
        self.current_lang = default_lang
        self.available_langs = self.get_available_languages()
        self.strings = {}
        self.load_language(default_lang)
    
    def get_available_languages(self):
        """Get list of available language files"""
        # Get base path for bundled resources
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        else:
            # Running as script
            base_path = Path(__file__).parent
        
        # Try different paths to find the lang directory
        possible_paths = [
            base_path / 'lang',              # Bundled resources
            Path(__file__).parent / 'lang',  # When run as module
            Path('.') / 'lang',              # When run from current directory
            Path(os.getcwd()) / 'lang'       # Current working directory
        ]
        
        lang_dir = None
        for path in possible_paths:
            if path.exists() and path.is_dir():
                lang_dir = path
                break
        
        if lang_dir is None:
            print("Warning: lang directory not found, defaulting to English")
            return ['en']
        
        langs = []
        for file in lang_dir.glob('*.json'):
            langs.append(file.stem)
        
        print(f"Found languages: {langs}")  # Debug output
        return sorted(langs) if langs else ['en']
    
    def load_language(self, lang_code):
        """Load language strings from JSON file"""
        try:
            print(f"Attempting to load language: {lang_code}")  # Debug
            
            # Get base path for bundled resources
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller bundle
                base_path = Path(sys._MEIPASS)
            else:
                # Running as script
                base_path = Path(__file__).parent
            
            # Find the language file
            possible_paths = [
                base_path / 'lang' / f'{lang_code}.json',              # Bundled resources
                Path(__file__).parent / 'lang' / f'{lang_code}.json',  # When run as module
                Path('.') / 'lang' / f'{lang_code}.json',              # When run from current directory
                Path(os.getcwd()) / 'lang' / f'{lang_code}.json'       # Current working directory
            ]
            
            lang_file = None
            for path in possible_paths:
                if path.exists():
                    lang_file = path
                    break
            
            if lang_file is None:
                raise FileNotFoundError(f"Language file for '{lang_code}' not found")
            
            # Load JSON data
            with open(lang_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Store the strings (convert keys to uppercase for compatibility)
            self.strings = {
                'MAIN': data.get('main', {}),
                'MENU': data.get('menu', {}),
                'MESSAGES': data.get('messages', {}),
                'DIALOGS': data.get('dialogs', {}),
                'ABOUT': data.get('about', {})
            }
            
            self.current_lang = lang_code
            print(f"Successfully loaded language: {lang_code}")  # Debug
            return True
            
        except FileNotFoundError as e:
            print(f"File not found for '{lang_code}': {e}")
            if lang_code != 'en':
                return self.load_language('en')
            return False
        except json.JSONDecodeError as e:
            print(f"JSON decode error for '{lang_code}': {e}")
            if lang_code != 'en':
                return self.load_language('en')
            return False
        except Exception as e:
            print(f"Error loading language '{lang_code}': {e}")
            if lang_code != 'en':
                return self.load_language('en')
            return False
    
    def get_string(self, category, key, default=None):
        """Get a translated string"""
        if default is None:
            default = f"{category}.{key}"
        
        return self.strings.get(category, {}).get(key, default)
    
    def get_main(self, key, default=None):
        """Get main application string"""
        return self.get_string('MAIN', key, default)
    
    def get_menu(self, key, default=None):
        """Get menu string"""
        return self.get_string('MENU', key, default)
    
    def get_message(self, key, default=None):
        """Get message string"""
        return self.get_string('MESSAGES', key, default)
    
    def get_dialog(self, key, default=None):
        """Get dialog string"""
        return self.get_string('DIALOGS', key, default)
    
    def get_about(self, key, default=None):
        """Get about dialog string"""
        return self.get_string('ABOUT', key, default)
    
    def switch_language(self, lang_code):
        """Switch to a different language"""
        if lang_code in self.available_langs:
            return self.load_language(lang_code)
        return False
    
    def get_language_names(self):
        """Get human-readable language names"""
        names = {
            'en': 'English',
            'ko': '한국어 (Korean)',
            'ja': '日本語 (Japanese)',
            'zh': '中文 (Chinese)',
            'es': 'Español (Spanish)',
            'fr': 'Français (French)',
            'de': 'Deutsch (German)',
            'it': 'Italiano (Italian)',
            'pt': 'Português (Portuguese)',
            'ru': 'Русский (Russian)'
        }
        
        return {lang: names.get(lang, lang.upper()) for lang in self.available_langs}

# Global language manager instance
_lang_manager = None

def get_lang_manager():
    """Get the global language manager instance"""
    global _lang_manager
    if _lang_manager is None:
        _lang_manager = LanguageManager()
    return _lang_manager

def init_language(lang_code='en'):
    """Initialize the language system"""
    global _lang_manager
    _lang_manager = LanguageManager(lang_code)
    return _lang_manager

# Convenience functions for getting strings
def _(category, key, default=None):
    """Get translated string (short form)"""
    return get_lang_manager().get_string(category, key, default)

def get_main(key, default=None):
    """Get main application string"""
    return get_lang_manager().get_main(key, default)

def get_menu(key, default=None):
    """Get menu string"""
    return get_lang_manager().get_menu(key, default)

def get_message(key, default=None):
    """Get message string"""
    return get_lang_manager().get_message(key, default)

def get_dialog(key, default=None):
    """Get dialog string"""
    return get_lang_manager().get_dialog(key, default)

def get_about(key, default=None):
    """Get about dialog string"""
    return get_lang_manager().get_about(key, default)
