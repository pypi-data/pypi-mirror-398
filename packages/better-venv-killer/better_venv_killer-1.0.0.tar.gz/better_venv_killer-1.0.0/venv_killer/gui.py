#!/usr/bin/env python3
"""
GUI interface for venv-killer
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import shutil
import sys
from pathlib import Path

from .core import (
    scan_directory_optimized,
    format_size,
    parse_size,
)


class VenvKillerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Environment Killer")
        self.root.geometry("900x700")
        
        # Variables
        self.scan_paths = []
        self.found_venvs = []
        self.selected_venvs = []
        
        # Create GUI
        self.create_widgets()
        
        # Set default values
        self.max_depth_var.set("10")
        self.add_path(str(Path.home()))
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Scan Paths Section
        ttk.Label(main_frame, text="Scan Paths:", font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        paths_frame = ttk.Frame(main_frame)
        paths_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        paths_frame.columnconfigure(0, weight=1)
        
        self.paths_listbox = tk.Listbox(paths_frame, height=3)
        self.paths_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        paths_buttons_frame = ttk.Frame(paths_frame)
        paths_buttons_frame.grid(row=0, column=1, sticky=tk.N)
        
        ttk.Button(paths_buttons_frame, text="Add Folder", command=self.browse_folder).grid(row=0, column=0, pady=(0, 2))
        ttk.Button(paths_buttons_frame, text="Remove", command=self.remove_path).grid(row=1, column=0, pady=(0, 2))
        ttk.Button(paths_buttons_frame, text="Clear All", command=self.clear_paths).grid(row=2, column=0)
        
        # Options Section
        options_frame = ttk.LabelFrame(main_frame, text="Scan Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # Include Conda
        self.include_conda_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Include Conda environments", 
                       variable=self.include_conda_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Max Depth
        ttk.Label(options_frame, text="Max Depth:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.max_depth_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.max_depth_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=(0, 5))
        
        # Min Size
        ttk.Label(options_frame, text="Min Size:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.min_size_var = tk.StringVar()
        min_size_frame = ttk.Frame(options_frame)
        min_size_frame.grid(row=2, column=1, sticky=tk.W, pady=(0, 5))
        ttk.Entry(min_size_frame, textvariable=self.min_size_var, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Label(min_size_frame, text="(e.g., 100MB, 1GB)").grid(row=0, column=1)
        
        # Older Than
        ttk.Label(options_frame, text="Older Than:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        self.older_than_var = tk.StringVar()
        older_than_frame = ttk.Frame(options_frame)
        older_than_frame.grid(row=3, column=1, sticky=tk.W, pady=(0, 5))
        ttk.Entry(older_than_frame, textvariable=self.older_than_var, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Label(older_than_frame, text="days").grid(row=0, column=1)
        
        # Dry Run
        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Dry Run (preview only)", 
                       variable=self.dry_run_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Scan Button
        ttk.Button(main_frame, text="🔍 Scan for Environments", 
                  command=self.start_scan).grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready to scan...")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="Found Environments", padding="10")
        results_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Treeview for results
        columns = ('Select', 'Path', 'Size', 'Age', 'Type')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        for col in columns:
            self.results_tree.heading(col, text=col)
        
        self.results_tree.column('Select', width=60, minwidth=60)
        self.results_tree.column('Path', width=400, minwidth=200)
        self.results_tree.column('Size', width=80, minwidth=80)
        self.results_tree.column('Age', width=80, minwidth=80)
        self.results_tree.column('Type', width=60, minwidth=60)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Selection buttons
        selection_frame = ttk.Frame(results_frame)
        selection_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(selection_frame, text="Select All", command=self.select_all).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(selection_frame, text="Select None", command=self.select_none).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(selection_frame, text="Select Large (>100MB)", command=self.select_large).grid(row=0, column=2, padx=(0, 5))
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=7, column=0, columnspan=3, pady=(0, 10))
        
        self.delete_button = ttk.Button(action_frame, text="🗑️ Delete Selected", 
                                       command=self.delete_selected, state=tk.DISABLED)
        self.delete_button.grid(row=0, column=0, padx=(0, 10))
        
        self.total_size_var = tk.StringVar(value="Total: 0 B")
        ttk.Label(action_frame, textvariable=self.total_size_var, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=1)
        
        # Bind events
        self.results_tree.bind('<Button-1>', self.on_tree_click)
    
    def add_path(self, path):
        """Add a path to the scan list."""
        if path and path not in self.scan_paths:
            self.scan_paths.append(path)
            self.paths_listbox.insert(tk.END, path)
    
    def browse_folder(self):
        """Browse for a folder to add to scan paths."""
        folder = filedialog.askdirectory(title="Select folder to scan")
        if folder:
            self.add_path(folder)
    
    def remove_path(self):
        """Remove selected path from scan list."""
        selection = self.paths_listbox.curselection()
        if selection:
            index = selection[0]
            self.paths_listbox.delete(index)
            del self.scan_paths[index]
    
    def clear_paths(self):
        """Clear all scan paths."""
        self.paths_listbox.delete(0, tk.END)
        self.scan_paths.clear()
    
    def update_progress(self, message):
        """Update progress message."""
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def start_scan(self):
        """Start scanning in a separate thread."""
        if not self.scan_paths:
            messagebox.showwarning("No Paths", "Please add at least one path to scan.")
            return
        
        # Validate inputs
        try:
            max_depth = int(self.max_depth_var.get()) if self.max_depth_var.get() else 10
        except ValueError:
            messagebox.showerror("Invalid Input", "Max depth must be a number.")
            return
        
        min_size_bytes = 0
        if self.min_size_var.get():
            try:
                min_size_bytes = parse_size(self.min_size_var.get())
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))
                return
        
        older_than_days = 0
        if self.older_than_var.get():
            try:
                older_than_days = int(self.older_than_var.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Older than must be a number of days.")
                return
        
        # Start scanning
        self.progress_bar.start()
        self.delete_button.config(state=tk.DISABLED)
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.found_venvs.clear()
        
        # Start scan in thread
        thread = threading.Thread(target=self.scan_thread, 
                                args=(max_depth, min_size_bytes, older_than_days))
        thread.daemon = True
        thread.start()
    
    def scan_thread(self, max_depth, min_size_bytes, older_than_days):
        """Scanning thread function."""
        try:
            all_venvs = []
            
            for path_str in self.scan_paths:
                path = Path(path_str)
                if not path.exists():
                    continue
                
                self.update_progress(f"Scanning {path}...")
                
                found_venvs = scan_directory_optimized(
                    path, 
                    max_depth, 
                    self.include_conda_var.get(),
                    self.update_progress
                )
                all_venvs.extend(found_venvs)
            
            # Apply filters
            if min_size_bytes > 0:
                all_venvs = [(path, size, age, env_type) for path, size, age, env_type in all_venvs 
                           if size >= min_size_bytes]
            
            if older_than_days > 0:
                all_venvs = [(path, size, age, env_type) for path, size, age, env_type in all_venvs 
                           if age >= older_than_days]
            
            # Sort by size (largest first)
            all_venvs.sort(key=lambda x: x[1], reverse=True)
            
            # Update GUI in main thread
            self.root.after(0, self.scan_complete, all_venvs)
            
        except Exception as e:
            self.root.after(0, self.scan_error, str(e))
    
    def scan_complete(self, venvs):
        """Handle scan completion."""
        self.progress_bar.stop()
        self.found_venvs = venvs
        
        if not venvs:
            self.update_progress("No environments found matching criteria.")
            return
        
        self.update_progress(f"Found {len(venvs)} environment(s)")
        
        # Populate treeview
        for path, size, age, env_type in venvs:
            age_str = f"{age}d" if age > 0 else "0d"
            item = self.results_tree.insert('', tk.END, 
                                          values=('☐', str(path), format_size(size), age_str, env_type))
        
        self.update_total_size()
        self.delete_button.config(state=tk.NORMAL)
    
    def scan_error(self, error_msg):
        """Handle scan error."""
        self.progress_bar.stop()
        self.update_progress("Scan failed.")
        messagebox.showerror("Scan Error", f"Error during scan: {error_msg}")
    
    def on_tree_click(self, event):
        """Handle tree click for checkbox simulation."""
        region = self.results_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.results_tree.identify_row(event.y)
            column = self.results_tree.identify_column(event.x)
            
            # Only handle clicks on the Select column
            if item and column == '#1':  # First column (Select)
                # Toggle selection
                current_values = list(self.results_tree.item(item, 'values'))
                if item in self.selected_venvs:
                    self.selected_venvs.remove(item)
                    current_values[0] = '☐'
                else:
                    self.selected_venvs.append(item)
                    current_values[0] = '☑'
                
                self.results_tree.item(item, values=current_values)
                self.update_total_size()
    
    def select_all(self):
        """Select all environments."""
        self.selected_venvs.clear()
        for item in self.results_tree.get_children():
            self.selected_venvs.append(item)
            current_values = list(self.results_tree.item(item, 'values'))
            current_values[0] = '☑'
            self.results_tree.item(item, values=current_values)
        self.update_total_size()
    
    def select_none(self):
        """Deselect all environments."""
        for item in self.results_tree.get_children():
            current_values = list(self.results_tree.item(item, 'values'))
            current_values[0] = '☐'
            self.results_tree.item(item, values=current_values)
        self.selected_venvs.clear()
        self.update_total_size()
    
    def select_large(self):
        """Select environments larger than 100MB."""
        self.select_none()
        for i, (path, size, age, env_type) in enumerate(self.found_venvs):
            if size > 100 * 1024 * 1024:  # 100MB
                item = self.results_tree.get_children()[i]
                self.selected_venvs.append(item)
                current_values = list(self.results_tree.item(item, 'values'))
                current_values[0] = '☑'
                self.results_tree.item(item, values=current_values)
        self.update_total_size()
    
    def update_total_size(self):
        """Update total size display."""
        total_size = 0
        for item in self.selected_venvs:
            index = self.results_tree.index(item)
            if index < len(self.found_venvs):
                total_size += self.found_venvs[index][1]
        
        self.total_size_var.set(f"Selected: {len(self.selected_venvs)} items, {format_size(total_size)}")
    
    def delete_selected(self):
        """Delete selected environments."""
        if not self.selected_venvs:
            messagebox.showwarning("No Selection", "Please select environments to delete.")
            return
        
        # Calculate total size
        total_size = 0
        selected_paths = []
        for item in self.selected_venvs:
            index = self.results_tree.index(item)
            if index < len(self.found_venvs):
                path, size, age, env_type = self.found_venvs[index]
                selected_paths.append((path, size))
                total_size += size
        
        if self.dry_run_var.get():
            # Show dry run results
            message = f"DRY RUN: Would delete {len(selected_paths)} environment(s)\n"
            message += f"Total size: {format_size(total_size)}\n\n"
            message += "Environments:\n"
            for path, size in selected_paths[:10]:  # Show first 10
                message += f"• {path} ({format_size(size)})\n"
            if len(selected_paths) > 10:
                message += f"... and {len(selected_paths) - 10} more"
            
            messagebox.showinfo("Dry Run Results", message)
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion", 
                                  f"Delete {len(selected_paths)} environment(s)?\n"
                                  f"Total size: {format_size(total_size)}\n\n"
                                  f"This action cannot be undone!"):
            return
        
        # Perform deletion
        self.progress_bar.start()
        self.update_progress("Deleting environments...")
        
        thread = threading.Thread(target=self.delete_thread, args=(selected_paths,))
        thread.daemon = True
        thread.start()
    
    def delete_thread(self, paths_to_delete):
        """Deletion thread function."""
        deleted_paths = []
        total_freed = 0
        errors = []
        
        for path, size in paths_to_delete:
            try:
                self.root.after(0, self.update_progress, f"Deleting {path}...")
                shutil.rmtree(path, ignore_errors=False)
                deleted_paths.append(str(path))
                total_freed += size
            except Exception as e:
                errors.append(f"{path}: {str(e)}")
        
        self.root.after(0, self.delete_complete, len(deleted_paths), total_freed, errors, deleted_paths)
    
    def delete_complete(self, deleted_count, total_freed, errors, deleted_paths):
        """Handle deletion completion."""
        self.progress_bar.stop()
        
        message = f"Deleted {deleted_count} environment(s)\n"
        message += f"Space freed: {format_size(total_freed)}"
        
        if errors:
            message += f"\n\nErrors ({len(errors)}):\n"
            message += "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                message += f"\n... and {len(errors) - 5} more errors"
        
        messagebox.showinfo("Deletion Complete", message)
        
        # Remove successfully deleted items from GUI and data
        items_to_remove = []
        for item in list(self.selected_venvs):  # Create copy to avoid modification during iteration
            index = self.results_tree.index(item)
            if index < len(self.found_venvs):
                path, size, age, env_type = self.found_venvs[index]
                # Check if this path was successfully deleted
                if str(path) in deleted_paths:
                    items_to_remove.append((item, index))
        
        # Remove from GUI and data (reverse order to maintain indices)
        for item, index in sorted(items_to_remove, key=lambda x: x[1], reverse=True):
            self.results_tree.delete(item)
            del self.found_venvs[index]
            if item in self.selected_venvs:
                self.selected_venvs.remove(item)
        
        # Update display
        self.update_total_size()
        
        # Update progress message
        remaining_count = len(self.found_venvs)
        if remaining_count == 0:
            self.update_progress("All environments deleted. Click scan to find more.")
        else:
            self.update_progress(f"Deletion complete. {remaining_count} environment(s) remaining.")


def main():
    try:
        root = tk.Tk()
        
        # Set window icon and properties
        root.resizable(True, True)
        root.minsize(800, 600)
        
        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        app = VenvKillerGUI(root)
        
        # Handle window close
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit VenvKiller?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())