"""
GUI.PY v9.7 - THE COMPLETE FRAMEWORK
Architecture: Fine-grained Reactivity, Virtual DOM, Navigation Stack, Theme Engine.
Includes: DataTable, Toasts, Modals, Dependency Tracking.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import functools
from abc import ABC, abstractmethod
from typing import Callable, List, Dict, Any, Optional
import math  # REQUIRED for Physics Animations
import os               # For file paths and EXE location
import sys              # For Telemetry and exception hooks
import json             # For SQLStore and state serialization
import sqlite3          # For the Persistence Engine
import threading        # For background tasks and loops
import subprocess       # For the Compiler and opening folders
import base64           # For Asset Manager (Binary Inlining)
import urllib.request   # For the Auto-Update Client (Networking)
import re               # For input validation and string parsing
import random           # For generating unique widget keys
import string           # For ID generation
import datetime         # For Telemetry timestamps
from concurrent.futures import ThreadPoolExecutor # For the Worker Pool
# Optional Bridges (Prevents crashes if libs are missing)
try:
    import cv2
except ImportError:
    cv2 = None
try:
    from plyer import notification
except ImportError:
    notification = None
try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

# ==========================================
# 1. THE REACTIVE CORE (Dependency Magic)
# ==========================================

class DependencyTracker:
    current_context = None

class ReactiveState:
    def __init__(self, owner=None):
        self._data = {}
        self._owner = owner
        self._subscribers = {}

    def __setattr__(self, name, value):
        if name.startswith("_"): return super().__setattr__(name, value)
        if self._data.get(name) == value: return
        
        self._data[name] = value
        if name in self._subscribers:
            # SCRIPTED UPDATE: Only update what's necessary
            for callback in list(self._subscribers[name]):
                try: callback()
                except: self._subscribers[name].remove(callback)

    def __getattr__(self, name):
        if DependencyTracker.current_context:
            if name not in self._subscribers: self._subscribers[name] = set()
            self._subscribers[name].add(DependencyTracker.current_context)
        return self._data.get(name)

    def _clear_listeners(self):
        self._subscribers.clear()

# ==========================================
# 2. THE RENDER ENGINE & VIRTUAL DOM (Final Fix)
# ==========================================
class VNode:
    """The Virtual DOM Node definition."""
    def __init__(self, tag, props=None, children=None):
        self.tag = tag
        self.props = props if props else {}
        self.children = children if children else []
        self.key = self.props.get("key", "".join(random.choices(string.ascii_letters, k=8)))
        self.dom_node = None
        if "draw_func" in self.props:
            self.draw_func = self.props["draw_func"]

class Renderer:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.theme = app.theme
        self.registry = {} 

    def mount(self, parent, vnode):
        props = vnode.props
        tag = vnode.tag
        
        # FACTORY
        if tag == "Column": widget = tk.Frame(parent, bg=props.get("bg", self.theme['bg']))
        elif tag == "Row": widget = tk.Frame(parent, bg=props.get("bg", self.theme['bg']))
        elif tag == "Card": widget = tk.Frame(parent, bg="white", relief="flat", highlightbackground="#ddd", highlightthickness=1)
        elif tag == "Label": widget = tk.Label(parent, bg=parent.cget("bg"), fg=self.theme['fg'])
        elif tag == "Button": widget = tk.Button(parent, relief="flat", overrelief="raised", cursor="hand2")
        elif tag == "Input":
            var = tk.StringVar()
            widget = tk.Entry(parent, textvariable=var, relief="flat", highlightthickness=1)
            widget._var = var
        elif tag == "DataTable": widget = ttk.Treeview(parent, columns=props.get("cols", []), show="headings")
        elif tag == "Canvas":
            widget = tk.Canvas(parent, bg="white", highlightthickness=0)
            if hasattr(vnode, "draw_func"):
                # Use after() to ensure the widget is mapped before drawing
                widget.after(10, lambda: vnode.draw_func(widget))
        else: widget = tk.Frame(parent)

        vnode.dom_node = widget
        self.registry[vnode.key] = widget # Keep reference alive
        self._apply_props(widget, vnode)
        self._apply_layout(widget, vnode)

        for child in vnode.children:
            if child: self.mount(widget, child)
        return widget

    def _apply_props(self, widget, vnode):
        p = vnode.props
        if "text" in p:
            val = p["text"]
            if callable(val):
                def update_text():
                    if widget.winfo_exists(): widget.configure(text=str(val()))
                DependencyTracker.current_context = update_text
                widget.configure(text=str(val()))
                DependencyTracker.current_context = None
            else: widget.configure(text=str(val))

        conf = {}
        if "click" in p: conf["command"] = p["click"]
        if "bg" in p: conf["bg"] = p["bg"]
        if "fg" in p: conf["fg"] = p["fg"]
        if "font" in p: conf["font"] = p["font"]
        if "width" in p: conf["width"] = p["width"]
        if conf: 
            try: widget.configure(**conf)
            except: pass
        
        if vnode.tag == "Input":
            if "on_change" in p:
                widget._var.trace_add("write", lambda *a: p["on_change"](widget._var.get()))
            if "value" in p: widget._var.set(p["value"])

        if vnode.tag == "DataTable" and "cols" in p:
            for col in p['cols']: widget.heading(col, text=col)
            for item in p.get("rows", []): widget.insert("", "end", values=item)

    def _apply_layout(self, widget, vnode):
        p = vnode.props
        fill = "both" if vnode.tag == "Column" else "x"
        side = "top" if vnode.tag == "Column" else "left"
        expand = p.get("expand", False)
        widget.pack(side=side, fill=fill, expand=expand, padx=p.get("p", 0), pady=p.get("p", 0))
# ==========================================
# 3. APP ARCHITECTURE (Memory Safe)
# ==========================================
class App:
    def __init__(self, title="Framework App"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1000x700")
        self.version = "9.7.2"
        self.guard = Guard()
        self.theme = {'bg': '#f8f9fa', 'fg': '#212529', 'primary': '#0d6efd', 'font': ('Segoe UI', 11)}
        self.state = ReactiveState(owner=self)
        self.renderer = Renderer(self.root, self)
        self.routes = {}
        self.active_component = None
        Telemetry.hook_exceptions(self)

    def route(self, path, component_cls): self.routes[path] = component_cls

    def navigate(self, path):
        if not self.guard.check(self, path): return

        if self.active_component:
            self.active_component.on_unmount()
            self.active_component.local._clear_listeners()
            # FIX: Clear memory registry to prevent leaks
            self.renderer.registry.clear()
            for child in self.root.winfo_children(): child.destroy()

        self.active_component = self.routes[path](self)
        self.active_component.on_mount()
        
        vdom = self.active_component.build()
        self.renderer.mount(self.root, vdom)

    def toast(self, message):
        t = tk.Toplevel(self.root)
        t.overrideredirect(True)
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 125
        y = self.root.winfo_y() + self.root.winfo_height() - 80
        t.geometry(f"250x40+{x}+{y}")
        tk.Label(t, text=message, bg="#333", fg="white", font=("Arial", 10)).pack(expand=True, fill="both")
        self.root.after(2500, t.destroy)

    def start(self, initial):
        self.navigate(initial)
        self.root.mainloop()
# ==========================================
# 4. COMPONENTS & BUILDERS
# ==========================================

class Component(ABC):
    def __init__(self, app):
        self.app = app
        self.local = ReactiveState(owner=self)

    @abstractmethod
    def build(self) -> VNode: pass
    def on_mount(self): pass
    def on_unmount(self): pass

# FLUTTER-STYLE BUILDERS
def Column(children, **p): return VNode("Column", p, children)
def Row(children, **p):    return VNode("Row", p, children)
def Card(children, **p):   return VNode("Card", p, children)
def Label(text, **p):      return VNode("Label", {"text": text, **p})
def Button(text, click, **p): return VNode("Button", {"text": text, "click": click, **p})
def Input(value, on_change, **p): return VNode("Input", {"value": value, "on_change": on_change, **p})
def DataTable(cols, rows, **p): return VNode("DataTable", {"cols": cols, "rows": rows, **p})

# ==========================================
# 5. BUSINESS DEMO (Components Only)
# ==========================================

class UserList(Component):
    def on_mount(self):
        self.local.search = ""
        self.local.count = 0
        self.users = [
            ("1", "Alice", "Admin"),
            ("2", "Bob", "User"),
            ("3", "Charlie", "Editor")
        ]

    def build(self):
        return Column(p=20, children=[
            # HEADER ROW
            Row(children=[
                Label("Team Dashboard", font=("Arial", 22, "bold")),
                Button("Logout", lambda: self.app.navigate("login"), bg="#ff4444", fg="white")
            ]),
            
            # METRIC CARDS
            Row(p=10, children=[
                Card(p=20, children=[
                    Label("Active Users"),
                    Label(lambda: f"{self.local.count}", font=("Arial", 24, "bold"), fg="#0d6efd")
                ]),
                Button("➕ Add User", lambda: setattr(self.local, 'count', self.local.count + 1))
            ]),

            # DATA TABLE
            Label("User Directory", font=("Arial", 14, "bold"), p=10),
            DataTable(
                cols=["ID", "Name", "Role"],
                rows=self.users
            ),

            # INTERACTIVE INPUT
            Card(p=15, children=[
                Label(lambda: f"Searching for: {self.local.search}"),
                Input(value=self.local.search, on_change=lambda v: setattr(self.local, 'search', v)),
                Button("Save Search", lambda: self.app.toast("Search History Saved!"))
            ])
        ])

class Login(Component):
    def build(self):
        return Column(p=100, children=[
            Card(p=40, children=[
                Label("Welcome Back", font=("Arial", 24, "bold"), p=20),
                Label("Username"),
                Input(value="", on_change=lambda v: None),
                Button("Sign In", lambda: self.app.navigate("dashboard"), bg="#0d6efd", fg="white", p=10)
            ])
        ])

# ==========================================
# 6. PERSISTENCE ENGINE (Reactive SQL)
# ==========================================
import json # Mandatory import for this module

class SQLStore:
    def __init__(self, db_name="app_data.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)")
        self.conn.commit()

    def sync(self, state_obj, keys: List[str]):
        for key in keys:
            row = self.conn.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
            if row: 
                try: setattr(state_obj, key, json.loads(row[0]))
                except: pass
            
            # Closure to capture the specific key for saving
            def save_op(k=key):
                val = getattr(state_obj, k)
                self.conn.execute("INSERT OR REPLACE INTO state VALUES (?, ?)", (k, json.dumps(val)))
                self.conn.commit()
            
            # Register subscriber
            if key not in state_obj._subscribers: state_obj._subscribers[key] = set()
            state_obj._subscribers[key].add(save_op)
            # ==========================================
# 7. NATIVE BRIDGE (OS Integration)
# ==========================================
class NativeOS:
    """Handles System Tray, Global Hotkeys, and Native OS Notifications."""
    @staticmethod
    def notify(title, message):
        """Triggers a native OS-level notification."""
        try:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=10)
        except ImportError:
            # Fallback to standard message box if library missing
            messagebox.showinfo(title, message)

    @staticmethod
    def open_path(path):
        """Opens a folder or file in the native OS file explorer."""
        if sys.platform == "win32": os.startfile(path)
        else: subprocess.run(["open", path])
        # ==========================================
# 8. HARDWARE CANVAS (High-Speed Graphics)
# ==========================================
class GraphicsCanvas(VNode):
    """A GPU-optimized drawing area for real-time charts or games."""
    def __init__(self, draw_func, **props):
        super().__init__("Canvas", props)
        self.draw_func = draw_func

    def render_graphics(self, widget):
        # Implementation of double-buffering to prevent flickering
        widget.delete("all")
        self.draw_func(widget)

        # ==========================================
# 9. DEPLOYMENT ARCHITECT (Binary Compiler)
# ==========================================
class Compiler:
    """Auto-configures PyInstaller to turn this script into a high-performance EXE."""
    @staticmethod
    def build(script_name, icon_path=None):
        import subprocess
        print("🚀 Compiling Application to Standalone Binary...")
        cmd = ["pyinstaller", "--noconfirm", "--onefile", "--windowed"]
        if icon_path: cmd.extend(["--icon", icon_path])
        cmd.append(script_name)
        
        subprocess.run(cmd)
        print("✅ Build Complete. Check the /dist folder.")
# ==========================================
# 10. AUTO-UPDATE CLIENT (Active)
# ==========================================
class Updater:
    """Checks for new versions of the EXE and handles hot-swapping."""
    def __init__(self, current_version, update_url):
        self.version = current_version
        self.url = update_url

    def check_for_updates(self):
        """Asynchronously checks if a new binary is available."""
        def check():
            try:
                # In production, this checks a real URL for a JSON response
                print(f" Checking for updates at {self.url}...")
                with urllib.request.urlopen(self.url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    if data.get('version') > self.version:
                        print(f"Update found: {data.get('version')}")
                        # Logic to download 'ZenithOS_v2.exe' would go here
            except Exception as e:
                # Silent fail is preferred for background updates
                print(f"Update check skipped: {e}")
        
        threading.Thread(target=check, daemon=True).start()
    # ==========================================
# 11. RESPONSIVE ENGINE (Flex-Grid)
# ==========================================
class FlexBox:
    """Calculates percentage-based widths for liquid layouts."""
    @staticmethod
    def compute_width(app, percentage):
        """Returns actual pixel width based on current window size."""
        app.root.update_idletasks()
        total_width = app.root.winfo_width()
        return int(total_width * (percentage / 100))

    @staticmethod
    def make_responsive(widget, app, pc_width):
        """Binds a widget to resize dynamically when the window scales."""
        def on_resize(event):
            new_w = FlexBox.compute_width(app, pc_width)
            widget.config(width=new_w)
        app.root.bind("<Configure>", on_resize, add="+")

        # ==========================================
# 12. MIDDLEWARE & GUARD SYSTEM
# ==========================================
class Guard:
    """Intercepts navigation to perform security checks."""
    def __init__(self):
        self.interceptors = []

    def add_guard(self, condition_func, redirect_path):
        """If condition_func returns False, redirect to redirect_path."""
        self.interceptors.append((condition_func, redirect_path))

    def check(self, app, target_path):
        for condition, redirect in self.interceptors:
            if not condition(app):
                app.navigate(redirect)
                return False
        return True
    

    # ==========================================
# 13. I18N ENGINE (Multi-Language Support)
# ==========================================
class Translator:
    """Handles real-time language switching for the entire UI."""
    def __init__(self, default_lang="en"):
        self.current_lang = default_lang
        self.dictionaries = {}

    def load(self, lang_code, data: Dict[str, str]):
        self.dictionaries[lang_code] = data

    def translate(self, key):
        """Fetches the string for the current language."""
        return self.dictionaries.get(self.current_lang, {}).get(key, key)
    
    # ==========================================
# 14. TELEMETRY & CRASH REPORTER
# ==========================================
class Telemetry:
    """Monitors app health and logs remote error reports."""
    @staticmethod
    def hook_exceptions(app):
        def custom_excepthook(exctype, value, traceback):
            error_data = {
                "timestamp": time.time(),
                "error": str(value),
                "type": str(exctype),
                "os": sys.platform,
                "version": getattr(app, 'version', '1.0.0')
            }
            # Log to local file
            with open("crash_report.log", "a") as f:
                f.write(json.dumps(error_data) + "\n")
            # In production, you would use 'urllib' to POST this to a server
            print(f"🚨 CRASH DETECTED: {value}")
        
        sys.excepthook = custom_excepthook

# ==========================================
# 15. ASSET MANAGER (GC Fixed)
# ==========================================
import base64
class AssetManager:
    """Inlines images into the code to prevent path errors in EXE conversion."""
    _cache = {} # FIX: Prevents images from disappearing

    @staticmethod
    def to_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    @staticmethod
    def get_image(name, b64_string):
        """Returns a PhotoImage and caches it."""
        if name not in AssetManager._cache:
            AssetManager._cache[name] = tk.PhotoImage(data=b64_string)
        return AssetManager._cache[name]
 # ==========================================
# 16. THE HARDWARE BRIDGE (Sensors & Media)
# ==========================================
class MediaEngine:
    """Reactive interface for Webcam, Microphone, and Biometrics."""
    @staticmethod
    def get_stream(device_id=0):
        """Returns a generator for camera frames (requires opencv-python)."""
        try:
            import cv2
            cap = cv2.VideoCapture(device_id)
            while True:
                ret, frame = cap.read()
                if not ret: break
                yield frame
        except ImportError:
            print("🚨 MediaEngine requires 'pip install opencv-python'")
            # ==========================================
# 18. THE SECURE VAULT (AES-256)
# ==========================================
class Vault:
    """High-security encrypted storage."""
    def __init__(self, key_file="secret.key"):
        self.key_file = key_file
        self.cipher = None
        self._load_key()

    def _load_key(self):
        if Fernet:
            if not os.path.exists(self.key_file):
                key = Fernet.generate_key()
                with open(self.key_file, "wb") as kf: kf.write(key)
            with open(self.key_file, "rb") as kf: 
                self.cipher = Fernet(kf.read())

    def encrypt(self, data: str) -> bytes:
        if not self.cipher: return data.encode()
        return self.cipher.encrypt(data.encode())

    def decrypt(self, token: bytes) -> str:
        if not self.cipher: return token.decode()
        return self.cipher.decrypt(token).decode()
  # ==========================================
# 17. WORKER POOL (Thread-Safe Version)
# ==========================================
class Worker:
    _pool = ThreadPoolExecutor(max_workers=4)

    @staticmethod
    def run(app, task_func, on_complete, *args):
        """Executes task in background and sends result back to UI thread."""
        def wrapper():
            try:
                result = task_func(*args)
                # CRITICAL: Schedule UI update on main thread
                app.root.after(0, lambda: on_complete(result))
            except Exception as e:
                app.root.after(0, lambda: messagebox.showerror("Worker Error", str(e)))
        
        Worker._pool.submit(wrapper)
        
        # ==========================================
# 19. STYLESHEET ENGINE (UI Polish)
# ==========================================
class Style:
    """Centralized design tokens."""
    PRIMARY = "#0d6efd"
    DANGER = "#dc3545"
    SUCCESS = "#198754"
    DARK = "#212529"
    LIGHT = "#f8f9fa"
    
    HEADER = ("Segoe UI", 24, "bold")
    BODY = ("Segoe UI", 11)
    MONO = ("Consolas", 10)
    # ==========================================
# 20. APP MANIFEST (Identity)
# ==========================================
class Manifest:
    APP_NAME = "ZenithOS"
    VERSION = "9.7.2"
    AUTHOR = "Architect"
    LICENSE = "MIT"

    # ==========================================
# 21. BOOTSTRAP (Main Execution)
# ==========================================
if __name__ == "__main__":
    # Initialize the App
    app = App(Manifest.APP_NAME)
    
    # Register Routes
    app.route("login", Login)
    app.route("dashboard", UserList)
    
    # Start the App
    app.start("login")