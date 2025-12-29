#!/usr/bin/env python3
"""
sample-app - Development & Programming Tools Application
Created with Amatak WinApp Generator
"""

import tkinter as tk
from tkinter import ttk

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("sample-app")
        self.geometry("800x600")
        
        # Setup dark theme
        self.setup_theme()
        self.create_widgets()
        
    def setup_theme(self):
        """Configure dark mode theme"""
        self.configure(bg="#1e1e1e")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
        style.configure("TButton", background="#007acc", foreground="#ffffff")
        style.configure("TFrame", background="#1e1e1e")
        
    def create_widgets(self):
        """Create UI widgets"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="sample-app", 
                 font=("Segoe UI", 24, "bold"),
                 foreground="#007acc").pack(pady=20)
        
        ttk.Label(main_frame, text="Development & Programming Tools Application",
                 font=("Segoe UI", 12)).pack(pady=10)
        
        ttk.Label(main_frame, 
                 text="Welcome to your new application!\nThis app was created with Amatak WinApp Generator.",
                 justify="center").pack(pady=30)
        
        ttk.Button(main_frame, text="Get Started", width=20).pack(pady=10)
        
        ttk.Label(main_frame, text="© 2024 sample-app",
                 foreground="#666666").pack(side=tk.BOTTOM, pady=20)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
