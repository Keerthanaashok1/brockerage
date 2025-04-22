#!/usr/bin/env python3
import os
import sys
import platform
import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import datetime
import shutil

def create_dir_if_not_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            return f"Created directory: {directory}"
        except Exception as e:
            return f"Error creating directory {directory}: {str(e)}"
    return f"Directory already exists: {directory}"

def get_app_path():
    """Get the path to the application bundle on macOS or executable on other platforms"""
    if getattr(sys, 'frozen', False):
        # Running as a bundled app
        if platform.system() == 'Darwin':  # macOS
            # For .app bundles, sys.executable points to the Python interpreter inside the bundle
            bundle_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))))
            return bundle_path
        else:
            # For other platforms when frozen
            return os.path.dirname(sys.executable)
    else:
        # Running as a script
        return os.path.dirname(os.path.abspath(__file__))

def get_resources_path():
    """Get the path to the resources directory where Excel files should be located"""
    if getattr(sys, 'frozen', False) and platform.system() == 'Darwin':
        # For macOS app bundle
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))), 'Resources')
    else:
        # For running as script or on other platforms
        return os.path.dirname(os.path.abspath(__file__))

def get_user_data_path():
    """Get the path to where user data (input/output) should be stored"""
    if platform.system() == 'Darwin':
        # On macOS, use Documents folder for user data
        home = os.path.expanduser('~')
        return os.path.join(home, 'Documents', 'BrokerageCalculator')
    else:
        # On other platforms, use the app directory
        return os.path.dirname(os.path.abspath(__file__))

def debug_info():
    """Gather debugging information"""
    info = []
    info.append(f"Python version: {sys.version}")
    info.append(f"Platform: {platform.platform()}")
    info.append(f"Current working directory: {os.getcwd()}")
    info.append(f"sys.executable: {sys.executable}")
    info.append(f"__file__: {__file__}")
    info.append(f"App path: {get_app_path()}")
    info.append(f"Resources path: {get_resources_path()}")
    info.append(f"User data path: {get_user_data_path()}")
    
    # Check if important files exist
    resources_path = get_resources_path()
    user_data_path = get_user_data_path()
    
    # Required Excel files
    nifty_param_path = os.path.join(resources_path, 'NIFTY_parameter.xlsx')
    nifty_input_path = os.path.join(resources_path, 'NIFTY_parameter_Input.xlsx')
    
    info.append(f"NIFTY_parameter.xlsx exists: {os.path.exists(nifty_param_path)}")
    info.append(f"NIFTY_parameter_Input.xlsx exists: {os.path.exists(nifty_input_path)}")
    
    # Input/Output directories
    input_dir = os.path.join(user_data_path, 'INPUT')
    output_dir = os.path.join(user_data_path, 'OUTPUT')
    
    info.append(create_dir_if_not_exists(user_data_path))
    info.append(create_dir_if_not_exists(input_dir))
    info.append(create_dir_if_not_exists(output_dir))
    
    # Check if we need to copy the template files to user data directory
    user_nifty_param = os.path.join(user_data_path, 'NIFTY_parameter.xlsx')
    user_nifty_input = os.path.join(user_data_path, 'NIFTY_parameter_Input.xlsx')
    
    if os.path.exists(nifty_param_path) and not os.path.exists(user_nifty_param):
        try:
            shutil.copy2(nifty_param_path, user_nifty_param)
            info.append(f"Copied NIFTY_parameter.xlsx to user data directory")
        except Exception as e:
            info.append(f"Error copying NIFTY_parameter.xlsx: {str(e)}")
    
    if os.path.exists(nifty_input_path) and not os.path.exists(user_nifty_input):
        try:
            shutil.copy2(nifty_input_path, user_nifty_input)
            info.append(f"Copied NIFTY_parameter_Input.xlsx to user data directory")
        except Exception as e:
            info.append(f"Error copying NIFTY_parameter_Input.xlsx: {str(e)}")
    
    return "\n".join(info)

def main():
    # Create the main window
    root = tk.Tk()
    root.title("Brokerage Calculator Debug")
    root.geometry("800x600")
    
    # Create a text widget to display the debug info
    text = tk.Text(root, wrap=tk.WORD)
    text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    # Insert the debug info
    debug_text = debug_info()
    text.insert(tk.END, debug_text)
    
    # Add a button to copy debug info to clipboard
    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(debug_text)
        messagebox.showinfo("Debug Info", "Debug information copied to clipboard.")
    
    copy_button = tk.Button(root, text="Copy Debug Info", command=copy_to_clipboard)
    copy_button.pack(pady=10)
    
    # Add a button to fix common issues
    def fix_issues():
        fixed_text = ""
        
        # Create user data directories
        user_data_path = get_user_data_path()
        input_dir = os.path.join(user_data_path, 'INPUT')
        output_dir = os.path.join(user_data_path, 'OUTPUT')
        
        fixed_text += create_dir_if_not_exists(user_data_path) + "\n"
        fixed_text += create_dir_if_not_exists(input_dir) + "\n"
        fixed_text += create_dir_if_not_exists(output_dir) + "\n"
        
        # Copy template files if needed
        resources_path = get_resources_path()
        nifty_param_path = os.path.join(resources_path, 'NIFTY_parameter.xlsx')
        nifty_input_path = os.path.join(resources_path, 'NIFTY_parameter_Input.xlsx')
        
        user_nifty_param = os.path.join(user_data_path, 'NIFTY_parameter.xlsx')
        user_nifty_input = os.path.join(user_data_path, 'NIFTY_parameter_Input.xlsx')
        
        if not os.path.exists(user_nifty_param):
            if os.path.exists(nifty_param_path):
                try:
                    shutil.copy2(nifty_param_path, user_nifty_param)
                    fixed_text += f"Copied NIFTY_parameter.xlsx to user data directory\n"
                except Exception as e:
                    fixed_text += f"Error copying NIFTY_parameter.xlsx: {str(e)}\n"
            else:
                fixed_text += f"Error: Source NIFTY_parameter.xlsx not found at {nifty_param_path}\n"
        
        if not os.path.exists(user_nifty_input):
            if os.path.exists(nifty_input_path):
                try:
                    shutil.copy2(nifty_input_path, user_nifty_input)
                    fixed_text += f"Copied NIFTY_parameter_Input.xlsx to user data directory\n"
                except Exception as e:
                    fixed_text += f"Error copying NIFTY_parameter_Input.xlsx: {str(e)}\n"
            else:
                fixed_text += f"Error: Source NIFTY_parameter_Input.xlsx not found at {nifty_input_path}\n"
        
        messagebox.showinfo("Fix Issues", fixed_text)
        
        # Refresh the debug info
        text.delete(1.0, tk.END)
        new_debug_text = debug_info()
        text.insert(tk.END, new_debug_text)
    
    fix_button = tk.Button(root, text="Fix Common Issues", command=fix_issues)
    fix_button.pack(pady=10)
    
    # Add a button to open the user data directory
    def open_user_data_dir():
        user_data_path = get_user_data_path()
        if os.path.exists(user_data_path):
            if platform.system() == 'Darwin':  # macOS
                os.system(f'open "{user_data_path}"')
            elif platform.system() == 'Windows':
                os.startfile(user_data_path)
            else:  # Linux
                os.system(f'xdg-open "{user_data_path}"')
        else:
            messagebox.showerror("Error", f"Directory does not exist: {user_data_path}")
    
    open_dir_button = tk.Button(root, text="Open User Data Directory", command=open_user_data_dir)
    open_dir_button.pack(pady=10)
    
    # Run the main loop
    root.mainloop()

if __name__ == "__main__":
    main()