from . import math_tools
from . import health
from . import cs_basics
from . import dal
from . import manual

# ==========================================
# THE CORE ENGINE (Data Science & AI)
# ==========================================
from . import aly  # AI: Neural Nets, GenAI, DataFrame, Math

# ==========================================
# SECURITY & NETWORKING
# ==========================================
from . import hack  # Ethical Hacking, Recon, Encryption

# ==========================================
# THE ZENITH GUI FRAMEWORK (v9.7)
# ==========================================
# This exposes the "World First" Desktop features
from .gui import (
    # 1. App Kernel & Architecture
    App, Component, ReactiveState, Manifest, Guard,
    
    # 2. UI Builders (Flutter-style)
    Column, Row, Card, Label, Button, Input, DataTable,
    
    # 3. High-Performance Graphics
    GraphicsCanvas,
    
    # 4. Advanced Engines (The "God-Tier" Modules)
    Worker,       # Background Threading
    MediaEngine,  # Camera/Microphone
    SQLStore,     # Reactive Database
    NativeOS,     # System Tray/Notifications
    Compiler,     # EXE Generator
    Updater,      # OTA Updates
    Vault,        # <--- ADDED: Secure Storage
    
    # 5. Utilities
    Style, Telemetry, AssetManager, Translator
)

# ==========================================
# THE SAY MODULE (CLI Framework)
# ==========================================
from .say import (
    # 1. Core Printing & Types
    say, t, dt, clear, 
    
    # 2. UI Structures & Visuals
    box, panel, tree, table, gradient, json_print,
    
    # 3. Smart Input & Menus
    ask, select,
    
    # 4. Status Indicators & Logging
    success, error, warn, info, log,
    
    # 5. Animations & Progress
    loading, progress, Spinner, walker, typewriter,
    
    # 6. File Manager (Easy CRUD & Data)
    save, read, lines, edit,
    read_csv, save_csv, read_json, save_json, 
    
    # 7. System & Networking
    run, fetch, load_env,
    
    # 8. String Mastery
    slug, cipher, extract, random_id,
    
    # 9. Developer Utils & Decorators
    inspect, track, retry, ago,

    # 10. Flow Control & Smart Loops
    repeat, every, until, chunks,

    # 11. Enterprise Safety
    safe_run, mask, throttle
)

# ==========================================
# OTHER UTILITIES
# ==========================================
from .cs_basics import benchmark 
from .dictionary import define

# Legacy Storage
from .storage import write_file, read_file, append_file, MiniDB

__version__ = "1.4.0" # Bumped: Added ZenithOS GUI Framework