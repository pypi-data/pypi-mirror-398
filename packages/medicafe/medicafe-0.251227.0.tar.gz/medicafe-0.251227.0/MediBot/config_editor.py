#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DOS-Style Config.json Editor
Interactive JSON configuration editor with DOS-like interface.
Compatible with Python 3.4.4 and Windows XP.
"""

import os
import sys
import json
from collections import OrderedDict

# Import our helper functions
from config_editor_helpers import (
    load_config_safe, create_backup, save_config_atomic, validate_json_structure,
    is_sensitive_key, get_value_type, format_value_for_display, clear_config_cache,
    get_nested_value, set_nested_value, get_path_string, validate_key_name, parse_value_input,
    resolve_config_path
)

class ConfigEditor:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = OrderedDict()
        self.original_config = OrderedDict()
        self.current_path = []  # List of keys representing current location
        self.staged_changes = []  # List of (path, old_value, new_value) tuples
        self.running = True
        
        # Load initial config
        self.config, error = load_config_safe(config_path)
        if error:
            print("WARNING: {}".format(error))
            print("Starting with empty configuration.")
            self.config = OrderedDict()
        
        # Keep a copy of original for comparison
        self.original_config = json.loads(json.dumps(self.config, ensure_ascii=False), object_pairs_hook=OrderedDict)
    
    def clear_screen(self):
        """Clear the console screen (XP compatible)."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print the editor header."""
        print("=" * 60)
        print("           MediCafe Config Editor")
        print("=" * 60)
        print("")
    
    def print_breadcrumb(self):
        """Print current navigation path."""
        path_str = get_path_string(self.current_path)
        print("Current Path: {}".format(path_str))
        print("-" * 60)
    
    def print_current_level(self):
        """Print the current level of the config tree."""
        current_data, found = get_nested_value(self.config, self.current_path)
        
        if not found:
            print("ERROR: Invalid path")
            return
        
        if not isinstance(current_data, dict):
            print("ERROR: Cannot navigate into non-object value")
            return
        
        if not current_data:
            print("(Empty object)")
            return
        
        # Print numbered items
        items = list(current_data.items())
        for i, (key, value) in enumerate(items, 1):
            value_display = format_value_for_display(value)
            value_type = get_value_type(value)
            
            # Mark sensitive keys
            sensitive_mark = " [SENSITIVE]" if is_sensitive_key(key) else ""
            
            print("[{}] {}: {} ({}){}".format(i, key, value_display, value_type, sensitive_mark))
    
    def print_commands(self):
        """Print available commands."""
        print("")
        print("Commands:")
        print("  [1-N] Navigate/Edit  [0] Back  [EDIT #] Edit  [ADD] Add Key")
        print("  [DIR] Refresh  [HELP] Help  [EXIT] Save & Exit")
        print("-" * 60)
    
    def print_help(self):
        """Print detailed help information."""
        self.clear_screen()
        self.print_header()
        print("HELP - Config Editor Commands")
        print("=" * 60)
        print("")
        print("Navigation:")
        print("  [1-N]     - Navigate into nested objects or edit simple values")
        print("  [0]       - Go back to parent level")
        print("  [..]      - Same as [0]")
        print("")
        print("Editing:")
        print("  [EDIT #]  - Edit the numbered item")
        print("  [ADD]     - Add a new key at current level")
        print("")
        print("Utilities:")
        print("  [DIR]     - Refresh current level display")
        print("  [HELP]    - Show this help screen")
        print("  [EXIT]    - Save changes and exit")
        print("  [Q]       - Same as [EXIT]")
        print("")
        print("Safety Features:")
        print("  - All changes are staged until you save")
        print("  - Automatic backup created before saving")
        print("  - Sensitive keys marked with [SENSITIVE]")
        print("  - Preview all changes before committing")
        print("")
        print("Press Enter to continue...")
        input()
    
    def navigate_to_item(self, item_number):
        """Navigate to a numbered item."""
        current_data, found = get_nested_value(self.config, self.current_path)
        
        if not found or not isinstance(current_data, dict):
            print("ERROR: Cannot navigate from current location")
            return
        
        items = list(current_data.items())
        if item_number < 1 or item_number > len(items):
            print("ERROR: Invalid item number")
            return
        
        key, value = items[item_number - 1]
        
        # If it's a simple value, offer to edit it
        if not isinstance(value, dict):
            self.edit_simple_value(key, value)
        else:
            # Navigate into the object
            self.current_path.append(key)
    
    def edit_simple_value(self, key, current_value):
        """Edit a simple (non-object) value."""
        current_type = get_value_type(current_value)
        current_display = format_value_for_display(current_value)
        
        print("")
        print("Editing: {}".format(key))
        print("Current value: {} ({})".format(current_display, current_type))
        print("")
        
        # Get new value
        new_value_str = input("Enter new value: ").strip()
        
        if not new_value_str:
            print("No changes made.")
            return
        
        # Parse the new value
        new_value, error = parse_value_input(new_value_str, current_type)
        if error:
            print("ERROR: {}".format(error))
            return
        
        # Show preview
        new_display = format_value_for_display(new_value)
        print("")
        print("Preview: {} -> {}".format(current_display, new_display))
        
        # Confirm change
        if is_sensitive_key(key):
            print("WARNING: This appears to be a sensitive key!")
        
        confirm = input("Apply this change? (Y/N): ").strip().upper()
        if confirm in ['Y', 'YES']:
            # Stage the change
            full_path = self.current_path + [key]
            self.staged_changes.append((full_path, current_value, new_value))
            set_nested_value(self.config, full_path, new_value)
            print("Change staged.")
        else:
            print("Change cancelled.")
    
    def add_new_key(self):
        """Add a new key at the current level."""
        current_data, found = get_nested_value(self.config, self.current_path)
        
        if not found or not isinstance(current_data, dict):
            print("ERROR: Cannot add key at current location")
            return
        
        print("")
        print("Add New Key")
        print("-" * 30)
        
        # Get key name
        while True:
            key_name = input("Enter key name: ").strip()
            is_valid, error = validate_key_name(key_name, current_data.keys())
            if is_valid:
                break
            print("ERROR: {}".format(error))
        
        # Get value type
        print("")
        print("Value types:")
        print("  1. string   - Text value")
        print("  2. number   - Numeric value")
        print("  3. boolean  - true/false")
        print("  4. array    - List of values")
        print("  5. object   - Nested structure")
        print("")
        
        while True:
            type_choice = input("Select value type (1-5): ").strip()
            type_map = {'1': 'string', '2': 'number', '3': 'boolean', '4': 'array', '5': 'object'}
            if type_choice in type_map:
                value_type = type_map[type_choice]
                break
            print("ERROR: Invalid choice. Enter 1-5.")
        
        # Get value based on type
        if value_type == 'string':
            value_input = input("Enter string value: ").strip()
        elif value_type == 'number':
            value_input = input("Enter number value: ").strip()
        elif value_type == 'boolean':
            value_input = input("Enter boolean value (true/false): ").strip()
        elif value_type == 'array':
            value_input = input("Enter array values (comma-separated): ").strip()
        elif value_type == 'object':
            value_input = ""  # Empty object
            print("Creating empty object. You can add keys to it later.")
        
        # Parse the value
        new_value, error = parse_value_input(value_input, value_type)
        if error:
            print("ERROR: {}".format(error))
            return
        
        # Show preview
        new_display = format_value_for_display(new_value)
        print("")
        print("Preview: {}: {} ({})".format(key_name, new_display, value_type))
        
        # Confirm addition
        if is_sensitive_key(key_name):
            print("WARNING: This appears to be a sensitive key!")
        
        confirm = input("Add this key? (Y/N): ").strip().upper()
        if confirm in ['Y', 'YES']:
            # Stage the change
            full_path = self.current_path + [key_name]
            self.staged_changes.append((full_path, None, new_value))
            set_nested_value(self.config, full_path, new_value)
            print("Key added and staged.")
        else:
            print("Addition cancelled.")
    
    def show_staged_changes(self):
        """Show all staged changes."""
        if not self.staged_changes:
            print("No staged changes.")
            return
        
        print("")
        print("Staged Changes:")
        print("-" * 30)
        
        for i, (path, old_value, new_value) in enumerate(self.staged_changes, 1):
            path_str = " > ".join(path)
            if old_value is None:
                print("{}. ADD: {} = {}".format(i, path_str, format_value_for_display(new_value)))
            else:
                print("{}. EDIT: {} = {} -> {}".format(
                    i, path_str, 
                    format_value_for_display(old_value), 
                    format_value_for_display(new_value)
                ))
    
    def save_changes(self):
        """Save all staged changes to file."""
        if not self.staged_changes:
            print("No changes to save.")
            return True
        
        print("")
        print("Saving Changes...")
        print("-" * 30)
        
        # Show summary
        self.show_staged_changes()
        print("")
        
        # Validate JSON structure
        is_valid, error = validate_json_structure(self.config)
        if not is_valid:
            print("ERROR: {}".format(error))
            return False
        
        # Create backup
        backup_path = create_backup(self.config_path)
        if backup_path:
            print("Backup created: {}".format(os.path.basename(backup_path)))
        else:
            print("WARNING: Could not create backup")
        
        # Save to file
        success, error = save_config_atomic(self.config_path, self.config)
        if not success:
            print("ERROR: {}".format(error))
            return False
        
        # Clear cache
        cache_success, cache_error = clear_config_cache()
        if not cache_success:
            print("WARNING: {}".format(cache_error))
        
        print("Configuration saved successfully!")
        return True
    
    def process_command(self, command):
        """Process a user command."""
        command = command.strip().upper()
        
        if command == 'EXIT' or command == 'Q':
            if self.staged_changes:
                print("")
                print("You have unsaved changes.")
                self.show_staged_changes()
                print("")
                save_choice = input("Save changes before exiting? (Y/N): ").strip().upper()
                if save_choice in ['Y', 'YES']:
                    if self.save_changes():
                        self.running = False
                else:
                    print("Changes discarded.")
                    self.running = False
            else:
                self.running = False
        
        elif command == 'HELP':
            self.print_help()
        
        elif command == 'DIR':
            pass  # Will refresh display
        
        elif command == 'ADD':
            self.add_new_key()
        
        elif command.startswith('EDIT '):
            try:
                item_num = int(command[5:].strip())
                self.navigate_to_item(item_num)
            except ValueError:
                print("ERROR: Invalid EDIT command. Use EDIT followed by a number.")
        
        elif command == '0' or command == '..':
            if self.current_path:
                self.current_path.pop()
            else:
                print("Already at root level.")
        
        elif command.isdigit():
            item_num = int(command)
            self.navigate_to_item(item_num)
        
        else:
            print("ERROR: Unknown command '{}'. Type HELP for available commands.".format(command))
    
    def run(self):
        """Main editor loop."""
        while self.running:
            self.clear_screen()
            self.print_header()
            self.print_breadcrumb()
            self.print_current_level()
            self.print_commands()
            
            if self.staged_changes:
                print("")
                print("You have {} unsaved changes.".format(len(self.staged_changes)))
            
            try:
                command = input("Config> ").strip()
                if command:
                    self.process_command(command)
            except KeyboardInterrupt:
                print("\n")
                print("Interrupted by user.")
                if self.staged_changes:
                    save_choice = input("Save changes before exiting? (Y/N): ").strip().upper()
                    if save_choice in ['Y', 'YES']:
                        self.save_changes()
                break
            except EOFError:
                break
        
        print("Config editor closed.")

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python config_editor.py <config_path>")
        sys.exit(1)
    
    # Resolve the config path using the same logic as MediLink_ConfigLoader
    default_path = sys.argv[1]
    config_path = resolve_config_path(default_path)
    
    # Ensure the directory exists (create it if needed)
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
        except OSError as e:
            # Ignore error if directory already exists (race condition)
            if e.errno != 17:  # EEXIST
                print("ERROR: Could not create config directory '{}': {}".format(config_dir, str(e)))
                sys.exit(1)
    
    editor = ConfigEditor(config_path)
    editor.run()

if __name__ == "__main__":
    main()
