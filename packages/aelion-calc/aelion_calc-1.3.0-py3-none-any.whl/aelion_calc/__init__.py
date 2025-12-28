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
from . import hack  # NEW: Ethical Hacking, Recon, Encryption

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
from .cs_basics import benchmark  # (retry is now in say, but keeping here if needed)
from .dictionary import define

# Legacy Storage (You can eventually replace this with say.save/read)
from .storage import write_file, read_file, append_file, MiniDB

__version__ = "1.3.0" # Bumped: Added Advanced CSV/JSON Data Handling