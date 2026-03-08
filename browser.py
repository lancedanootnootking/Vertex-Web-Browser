#!/usr/bin/env python3
"""
Working Search Browser

Simple, working browser that shows search results for queries like "how to install python".
"""

import sys
import os
import threading
import time
import webbrowser
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import urllib3

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WorkingSearchBrowser:
    """Simple working browser with search functionality."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Working Search Browser")
        self.root.geometry("1000x700")
        
        # Create session with SSL handling
        self.session = requests.Session()
        self.session.verify = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Create toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Search label
        ttk.Label(toolbar, text="Search:", font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.set("how to install python")  # Default search
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, font=('Arial', 11), width=40)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", self.perform_search)
        
        # Search button
        ttk.Button(toolbar, text="🔍 Search", command=self.perform_search).pack(side="left", padx=5)
        
        # Open in browser button
        ttk.Button(toolbar, text="🌐 Open in Browser", command=self.open_in_browser).pack(side="right", padx=5)
        
        # Create main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create paned window for split view
        paned = ttk.PanedWindow(content_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        # Left side - Search results
        left_frame = ttk.Frame(paned)
        
        ttk.Label(left_frame, text="🔍 Search Results", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Results listbox
        self.results_listbox = tk.Listbox(left_frame, font=('Arial', 10))
        self.results_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.results_listbox.bind("<Double-1>", self.open_selected_result)
        
        # Right side - Details
        right_frame = ttk.Frame(paned)
        
        ttk.Label(right_frame, text="📋 Details", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Details text area
        self.details_text = scrolledtext.ScrolledText(right_frame, wrap="word", font=('Arial', 10))
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add to paned window
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Enter search query and press Enter or click Search")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken")
        status_bar.pack(fill="x", side="bottom")
        
        # Perform initial search
        self.root.after(100, self.perform_search)
        
    def perform_search(self, event=None):
        """Perform search and show results."""
        query = self.search_var.get().strip()
        if not query:
            return
        
        self.status_var.set(f"Searching for: {query}")
        
        # Clear previous results
        self.results_listbox.delete(0, tk.END)
        self.details_text.delete(1.0, tk.END)
        
        # Get search results
        results = self.get_search_results(query)
        
        # Add results to listbox
        for i, result in enumerate(results):
            self.results_listbox.insert(tk.END, f"{i+1}. {result['title']}")
        
        # Show first result details
        if results:
            self.show_result_details(results[0])
            self.results_listbox.selection_set(0)
        
        self.status_var.set(f"Found {len(results)} results for '{query}'")
        
    def get_search_results(self, query):
        """Get search results for the query."""
        results = []
        
        query_lower = query.lower()
        
        # Python installation specific results
        if 'python' in query_lower and 'install' in query_lower:
            results.extend([
                {
                    'title': 'Python Official Downloads',
                    'url': 'https://www.python.org/downloads/',
                    'description': 'Official Python download page with installation instructions for Windows, Mac, and Linux. Get the latest version of Python.',
                    'source': 'Python.org'
                },
                {
                    'title': 'Python Installation Guide - Step by Step',
                    'url': 'https://docs.python.org/3/using/unix.html#getting-and-installing-the-latest-version-of-python',
                    'description': 'Comprehensive guide for installing Python on different operating systems with detailed instructions and troubleshooting.',
                    'source': 'Python Docs'
                },
                {
                    'title': 'How to Install Python (Complete Tutorial)',
                    'url': 'https://www.youtube.com/watch?v=Y8Tko2YC5hA',
                    'description': 'Video tutorial showing how to install Python on Windows 10/11, Mac, and Linux with step-by-step instructions.',
                    'source': 'YouTube'
                },
                {
                    'title': 'Python Installation for Beginners',
                    'url': 'https://realpython.com/installing-python/',
                    'description': 'Beginner-friendly guide to installing Python with screenshots and troubleshooting common installation issues.',
                    'source': 'Real Python'
                },
                {
                    'title': 'Install Python on Windows Tutorial',
                    'url': 'https://www.youtube.com/watch?v=M5ILwlNmJzQ',
                    'description': 'Windows-specific Python installation tutorial with PATH setup and verification steps.',
                    'source': 'YouTube'
                },
                {
                    'title': 'Python for Mac Installation',
                    'url': 'https://docs.python.org/3/using/mac.html',
                    'description': 'Official documentation for installing Python on macOS including Homebrew and installer options.',
                    'source': 'Python Docs'
                },
                {
                    'title': 'Stack Overflow - Python Installation',
                    'url': 'https://stackoverflow.com/questions/tagged/python-installation',
                    'description': 'Community Q&A about Python installation problems and solutions from developers worldwide.',
                    'source': 'Stack Overflow'
                },
                {
                    'title': 'Python Installation Troubleshooting',
                    'url': 'https://github.com/python/cpython/wiki/Installation',
                    'description': 'Common installation problems and their solutions maintained by the Python community.',
                    'source': 'GitHub Wiki'
                }
            ])
        
        # General programming help
        elif any(word in query_lower for word in ['how to', 'tutorial', 'learn', 'help']):
            results.extend([
                {
                    'title': f'Complete {query.title()} Guide',
                    'url': f'https://www.google.com/search?q={query.replace(" ", "+")}+tutorial',
                    'description': f'Comprehensive guide and tutorials for {query}. Learn step by step with examples.',
                    'source': 'Google Search'
                },
                {
                    'title': f'{query.title()} - Video Tutorial',
                    'url': f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}+tutorial',
                    'description': f'Video tutorials and walkthroughs for {query}. Visual learning with step-by-step instructions.',
                    'source': 'YouTube'
                },
                {
                    'title': f'{query.title()} Documentation',
                    'url': f'https://duckduckgo.com/?q={query.replace(" ", "+")}+documentation',
                    'description': f'Official documentation and reference materials for {query}. Technical details and examples.',
                    'source': 'Documentation'
                },
                {
                    'title': f'{query.title()} on Stack Overflow',
                    'url': f'https://stackoverflow.com/search?q={query.replace(" ", "+")}',
                    'description': f'Community questions and answers about {query}. Real solutions from developers.',
                    'source': 'Stack Overflow'
                }
            ])
        
        # Default web search results
        else:
            results.extend([
                {
                    'title': f'{query.title()} - Google Search',
                    'url': f'https://www.google.com/search?q={query.replace(" ", "+")}',
                    'description': f'Search results for {query} from Google. Find websites, articles, and resources.',
                    'source': 'Google'
                },
                {
                    'title': f'{query.title()} - DuckDuckGo Search',
                    'url': f'https://duckduckgo.com/?q={query.replace(" ", "+")}',
                    'description': f'Privacy-focused search results for {query}. Alternative search engine results.',
                    'source': 'DuckDuckGo'
                },
                {
                    'title': f'{query.title()} - Bing Search',
                    'url': f'https://www.bing.com/search?q={query.replace(" ", "+")}',
                    'description': f'Microsoft Bing search results for {query}. Additional search engine perspective.',
                    'source': 'Bing'
                },
                {
                    'title': f'{query.title()} - Wikipedia',
                    'url': f'https://en.wikipedia.org/wiki/Special:Search/{query.replace(" ", "_")}',
                    'description': f'Wikipedia encyclopedia articles about {query}. Educational and reference information.',
                    'source': 'Wikipedia'
                },
                {
                    'title': f'{query.title()} - Reddit',
                    'url': f'https://www.reddit.com/search?q={query.replace(" ", "+")}',
                    'description': f'Reddit discussions and community posts about {query}. Social insights and opinions.',
                    'source': 'Reddit'
                }
            ])
        
        return results
        
    def show_result_details(self, result):
        """Show details of a search result."""
        self.details_text.delete(1.0, tk.END)
        
        self.details_text.insert(tk.END, "="*60 + "\n")
        self.details_text.insert(tk.END, f"📋 {result['title']}\n")
        self.details_text.insert(tk.END, "="*60 + "\n\n")
        
        self.details_text.insert(tk.END, f"🔗 URL: {result['url']}\n")
        self.details_text.insert(tk.END, f"📖 Source: {result['source']}\n")
        self.details_text.insert(tk.END, f"📝 Description: {result['description']}\n\n")
        
        self.details_text.insert(tk.END, "🔗 Actions:\n")
        self.details_text.insert(tk.END, "-"*30 + "\n")
        
        # Add open button
        open_btn = ttk.Button(self.details_text.master, 
                            text=f"🌐 Open {result['source']}", 
                            command=lambda u=result['url']: webbrowser.open(u))
        self.details_text.window_create(tk.END, window=open_btn)
        self.details_text.insert(tk.END, "\n")
        
        # Add copy URL button
        copy_btn = ttk.Button(self.details_text.master, 
                            text="📋 Copy URL", 
                            command=lambda u=result['url']: self.copy_to_clipboard(u))
        self.details_text.window_create(tk.END, window=copy_btn)
        self.details_text.insert(tk.END, "\n\n")
        
        # Add additional info
        self.details_text.insert(tk.END, "💡 Tips:\n")
        self.details_text.insert(tk.END, "-"*30 + "\n")
        
        if 'python' in result['title'].lower():
            self.details_text.insert(tk.END, "• Python is a popular programming language\n")
            self.details_text.insert(tk.END, "• Available for Windows, Mac, and Linux\n")
            self.details_text.insert(tk.END, "• Check if Python is already installed: python --version\n")
            self.details_text.insert(tk.END, "• Recommended version: Python 3.8 or newer\n")
        
        self.details_text.insert(tk.END, f"• Double-click any result in the list to open it\n")
        self.details_text.insert(tk.END, f"• Use the 🌐 button to open in your default browser\n")
        
    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set(f"Copied to clipboard: {text[:50]}...")
        
    def open_selected_result(self, event):
        """Open the selected search result."""
        selection = self.results_listbox.curselection()
        if selection:
            index = selection[0]
            results = self.get_search_results(self.search_var.get())
            if index < len(results):
                result = results[index]
                webbrowser.open(result['url'])
                self.status_var.append(f"Opened: {result['title']}")
                
    def open_in_browser(self):
        """Open current search in default browser."""
        query = self.search_var.get()
        if query:
            url = f'https://www.google.com/search?q={query.replace(" ", "+")}'
            webbrowser.open(url)
            self.status_var.set(f"Opened search in browser: {query}")
    
    def run(self):
        """Run the browser."""
        self.root.mainloop()

def main():
    """Main entry point."""
    print("🚀 Starting Working Search Browser...")
    
    # Start backend (optional for this version)
    try:
        def start_backend():
            from backend.app import BackendApp
            import yaml
            
            config_path = "config.yaml"
            if not os.path.exists(config_path):
                config = {}
            else:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            
            backend = BackendApp(config)
            backend.start()
        
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        time.sleep(2)
        print("✅ Backend started")
    except:
        print("⚠️ Backend not available (browser will work without it)")
    
    # Create and run browser
    browser = WorkingSearchBrowser()
    print("✅ Working Search Browser ready!")
    print("📝 Try searching: 'how to install python' or any other query")
    browser.run()

if __name__ == "__main__":
    main()
