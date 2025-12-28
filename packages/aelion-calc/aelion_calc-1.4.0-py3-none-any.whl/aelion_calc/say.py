import sys
import time
import os
import datetime
import json as json_lib
import csv
import functools
from typing import Any, Dict, List
import threading
import itertools
import subprocess
import urllib.request
import urllib.error
import re
import random
import string
import getpass # For hidden password input

# --- CONSTANTS ---
dt = "TYPE_CHECK_MODE"

# --- ANSI CODES ---
COLORS = {
    'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
    'blue': '\033[94m', 'cyan': '\033[96m', 'magenta': '\033[95m',
    'white': '\033[97m', 'black': '\033[30m', 'reset': '\033[0m'
}
STYLES = {
    'bold': '\033[1m', 'underline': '\033[4m', 'italic': '\033[3m',
    'reset': '\033[0m'
}

# --- INTERNAL HELPERS ---
def _get_type_name(obj):
    return type(obj).__name__.upper()

def clear():
    """Clears the console screen (Windows/Linux/Mac)."""
    os.system('cls' if os.name == 'nt' else 'clear')

# --- MAIN PRINT FUNCTIONS ---

def t(*args, **kwargs):
    """Short alias for say()."""
    say(*args, **kwargs)

def say(*args, sep=' ', end='\n', color=None, style=None, loop=False):
    """
    Advanced Print Function.
    1. Normal: say("Hello", color='red')
    2. Type Check: say(my_var, dt)
    3. Sequence: say(start, inc, stop, loop=True)
    4. Auto-Box: say(my_dict) or say(my_list)
    """
    
    # MODE 1: TYPE CHECKING
    if len(args) == 2 and args[1] == "TYPE_CHECK_MODE":
        obj = args[0]
        formatted_text = f"{COLORS['cyan']}Type: {_get_type_name(obj)}{COLORS['reset']}"
        sys.stdout.write(formatted_text + end)
        return

    # MODE 2: NUMBER SEQUENCE
    if loop:
        if len(args) != 3:
            raise ValueError("Loop mode requires 3 arguments: say(start, inc, stop, loop=True)")
        start, inc, stop = args
        current = start
        while current <= stop:
            sys.stdout.write(f"{current}")
            if current + inc <= stop: sys.stdout.write(", ")
            current += inc
        sys.stdout.write(end)
        return

    # MODE 3: AUTO-DETECT DICT/LIST
    if len(args) == 1:
        if isinstance(args[0], dict):
            box(args[0], color=color or "blue")
            return
        # If it's a list of lists, try to print a table
        if isinstance(args[0], list) and len(args[0]) > 0 and isinstance(args[0][0], list):
            table(["Col "+str(i) for i in range(len(args[0][0]))], args[0], color=color or "green")
            return

    # MODE 4: NORMAL STYLED PRINT
    start_code = ""
    if color and color.lower() in COLORS: start_code += COLORS[color.lower()]
    if style and style.lower() in STYLES: start_code += STYLES[style.lower()]
        
    text = sep.join(map(str, args))
    
    if start_code:
        sys.stdout.write(f"{start_code}{text}{COLORS['reset']}{end}")
    else:
        sys.stdout.write(f"{text}{end}")

# ==========================================
# FEATURE: SMART INPUT v2.0
# ==========================================

def ask(question, type_expected=str, default=None, choices=None, validator=None, secure=False, error_msg=None):
    """
    Advanced Input Prompt.
    
    Parameters:
    - question (str): The prompt text.
    - type_expected (type): int, float, str, bool.
    - default (any): Value returned if user just hits Enter.
    - choices (list): Restrict input to these values.
    - validator (func): Lambda that returns True if input is valid.
    - secure (bool): If True, hides input (for passwords).
    """
    col = COLORS['yellow']
    rst = COLORS['reset']
    
    # 1. Build the prompt text visually
    prompt_text = f"{col}[?] {question}"
    
    if choices:
        prompt_text += f" ({'/'.join(map(str, choices))})"
    elif default is not None:
        prompt_text += f" [Default: {default}]"
        
    prompt_text += f": {rst}"

    while True:
        try:
            # 2. Get Input (Secure vs Normal)
            if secure:
                val_str = getpass.getpass(prompt_text)
            else:
                val_str = input(prompt_text)

            # 3. Handle Default (Empty Input)
            if not val_str:
                if default is not None:
                    return default
                if not secure: # Don't just loop on empty unless it's strictly required
                     continue

            # 4. Type Conversion
            val = val_str # Default is string
            
            if type_expected == int:
                val = int(val_str)
            elif type_expected == float:
                val = float(val_str)
            elif type_expected == bool:
                # Intelligent boolean parsing
                clean = val_str.lower()
                if clean in ['y', 'yes', '1', 'true', 't']: val = True
                elif clean in ['n', 'no', '0', 'false', 'f']: val = False
                else: raise ValueError("Not a boolean")
            
            # 5. Choices Check
            if choices and val not in choices:
                 say(f"Invalid choice. Must be one of: {choices}", color="red")
                 continue

            # 6. Custom Validator
            if validator:
                if not validator(val):
                     msg = error_msg or f"Input does not meet requirements."
                     say(msg, color="red")
                     continue

            return val

        except ValueError:
            say(f"Invalid format. Expected {type_expected.__name__}.", color="red")
# ==========================================
# FEATURE: TABLES (GRID)
# ==========================================

def table(headers, rows, color="cyan"):
    """
    Prints a neat grid table.
    Usage: say.table(["Name", "Score"], [["Ali", 90], ["Sim", 88]])
    """
    col_code = COLORS.get(color, COLORS['reset'])
    rst = COLORS['reset']
    
    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if len(str(cell)) > col_widths[i]:
                col_widths[i] = len(str(cell))
    
    # Create separator line
    border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    
    # Print Header
    print(f"{col_code}{border}")
    header_row = "|" + "|".join([f" {str(h).ljust(w)} " for h, w in zip(headers, col_widths)]) + "|"
    print(header_row)
    print(f"{border}{rst}")
    
    # Print Data
    for row in rows:
        data_row = "|" + "|".join([f" {str(cell).ljust(w)} " for cell, w in zip(row, col_widths)]) + "|"
        print(data_row)
    
    print(f"{col_code}{border}{rst}")

# ==========================================
# FEATURE: ANIMATIONS & BOXES
# ==========================================

def loading(seconds=3, message="Loading", color="green"):
    steps = 20
    delay = seconds / steps
    col_code = COLORS.get(color, COLORS['reset'])
    reset = COLORS['reset']
    
    sys.stdout.write(f"{message}: ")
    for i in range(steps + 1):
        filled = "#" * i
        empty = "." * (steps - i)
        bar = f"[{filled}{empty}]"
        sys.stdout.write(f"\r{col_code}{message}: {bar} {int(i/steps*100)}%{reset}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")

def box(data, title="INFO", color="blue"):
    col = COLORS.get(color, COLORS['reset'])
    rst = COLORS['reset']
    lines = []
    if isinstance(data, dict):
        for k, v in data.items(): lines.append(f"{k}: {v}")
    elif isinstance(data, list):
        lines = [str(x) for x in data]
    else: lines = [str(data)]

    width = max(len(line) for line in lines)
    if len(title) > width: width = len(title)
    width += 4

    print(f"{col}┌{'─' * width}┐")
    print(f"│ {title.center(width - 2)} │")
    print(f"├{'─' * width}┤")
    for line in lines: print(f"│ {line.ljust(width - 2)} │")
    print(f"└{'─' * width}┘{rst}")

    # ==========================================
# FEATURE: INTERACTIVE MENU
# ==========================================

def select(question, options):
    """
    Creates a numbered menu for the user to choose from.
    Returns the selected option (string).
    
    Usage: choice = say.select("Choose a color", ["Red", "Blue", "Green"])
    """
    col = COLORS['cyan']
    rst = COLORS['reset']
    
    print(f"\n{col}[?] {question}:{rst}")
    
    for i, opt in enumerate(options):
        print(f"   {i + 1}. {opt}")
        
    while True:
        try:
            choice = input(f"{COLORS['yellow']}Select (1-{len(options)}): {rst}")
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
            else:
                say("Invalid number. Try again.", color="red")
        except ValueError:
            say("Please enter a number.", color="red")

# ==========================================
# FEATURE: PRODUCTION LOGGING
# ==========================================

def log(message, level="INFO", filename="app.log"):
    """
    Writes a message to a file with a timestamp.
    Does NOT print to console (use say() for that).
    
    Levels: INFO, WARNING, ERROR, CRITICAL
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
    
    # Append to file
    with open(filename, "a", encoding="utf-8") as f:
        f.write(log_entry)

        # ==========================================
# FEATURE: STATUS SHORTCUTS
# ==========================================

def success(message):
    """Prints a green checkmark success message."""
    sys.stdout.write(f"{COLORS['green']}[✔] {message}{COLORS['reset']}\n")

def error(message):
    """Prints a red cross error message."""
    sys.stdout.write(f"{COLORS['red']}[✖] {message}{COLORS['reset']}\n")

def warn(message):
    """Prints a yellow warning message."""
    sys.stdout.write(f"{COLORS['yellow']}[!] {message}{COLORS['reset']}\n")

def info(message):
    """Prints a blue info message."""
    sys.stdout.write(f"{COLORS['blue']}[i] {message}{COLORS['reset']}\n")

# ==========================================
# FEATURE: CONTROLLABLE PROGRESS BAR
# ==========================================

def progress(iteration, total, prefix='Progress', suffix='', length=30, fill='█'):
    """
    Call in a loop to create a terminal progress bar.
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    
    # \r goes to start of line, end='' prevents new line
    sys.stdout.write(f'\r{COLORS["cyan"]}{prefix} |{bar}| {percent}% {suffix}{COLORS["reset"]}')
    
    # Print New Line on Complete
    if iteration == total: 
        sys.stdout.write('\n')
    sys.stdout.flush()

# ==========================================
# FEATURE: JSON SYNTAX HIGHLIGHTING
# ==========================================

def json_print(data):
    """
    Prints a dictionary or list as colored, indented JSON.
    Simulates syntax highlighting.
    """
    # Convert to formatted string first
    formatted_json = json_lib.dumps(data, indent=4)
    
    color_map = {
        '{': COLORS['white'], '}': COLORS['white'],
        '[': COLORS['white'], ']': COLORS['white'],
        ':': COLORS['white'], ',': COLORS['white']
    }
    
    # We process line by line to color keys and values differently
    lines = formatted_json.split('\n')
    for line in lines:
        # Highlight Keys (strings before a colon)
        if ':' in line:
            key, val = line.split(':', 1)
            # Color the Key Blue
            sys.stdout.write(f"{COLORS['blue']}{key}{COLORS['reset']}:")
            
            # Color the Value based on type
            val = val.strip()
            if val.startswith('"'): # String -> Green
                sys.stdout.write(f" {COLORS['green']}{val}{COLORS['reset']}")
            elif val == 'true' or val == 'false' or val == 'null': # Boolean/Null -> Red
                sys.stdout.write(f" {COLORS['red']}{val}{COLORS['reset']}")
            elif val.replace('.', '', 1).isdigit(): # Number -> Yellow
                sys.stdout.write(f" {COLORS['yellow']}{val}{COLORS['reset']}")
            else: # Structure ([ or {)
                sys.stdout.write(f" {val}")
        else:
            # Lines like "}," or "]"
            sys.stdout.write(f"{COLORS['white']}{line}{COLORS['reset']}")
            
        sys.stdout.write('\n')

# --- 1. THE PANEL (Boxed Layout) ---
def panel(text: str, title: str = "", color: str = "cyan", width: int = 50):
    """Prints text inside a bordered panel."""
    # Simple color mapping (you likely already have a color function)
    c_start = f"\033[96m" if color == "cyan" else "\033[94m" # simplified
    c_end = "\033[0m"
    
    horizontal = "─" * (width - 2)
    print(f"{c_start}╭{horizontal}╮{c_end}")
    
    if title:
        print(f"{c_start}│{c_end} {title.center(width - 4)} {c_start}│{c_end}")
        print(f"{c_start}├{horizontal}┤{c_end}")
        
    # Wrap text roughly (simplified for demo)
    print(f"{c_start}│{c_end} {text.ljust(width - 4)} {c_start}│{c_end}")
    print(f"{c_start}╰{horizontal}╯{c_end}")

# --- 2. THE TREE (Visual Hierarchy) ---
def tree(data: Dict[str, Any], prefix: str = ""):
    """Recursively prints a nested dictionary as a tree structure."""
    keys = list(data.keys())
    for i, key in enumerate(keys):
        is_last = (i == len(keys) - 1)
        connector = "└── " if is_last else "├── "
        
        print(f"{prefix}{connector}{key}")
        
        if isinstance(data[key], dict):
            extension = "    " if is_last else "│   "
            tree(data[key], prefix + extension)
        else:
            # Print the leaf value
            extension = "    " if is_last else "│   "
            print(f"{prefix}{extension}└── \033[90m{data[key]}\033[0m")

# --- 3. THE TRACKER (Performance Decorator) ---
def track(func):
    """Decorator: Logs execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        # Using your existing styles if available, or raw ANSI
        print(f"\n\033[1m[⏱ TIMER]\033[0m {func.__name__} took \033[93m{elapsed:.4f}s\033[0m")
        return result
    return wrapper

# ==========================================
# FEATURE: ADVANCED CONCURRENCY & DEBUG
# ==========================================

class Spinner:
    """
    A context manager that runs a loading animation on a separate thread
    WHILE your code executes.
    
    Usage:
        with say.Spinner("Connecting to DB"):
            time.sleep(3) # Your heavy work here
    """
    def __init__(self, message="Processing", color="cyan"):
        self.message = message
        self.color = color
        self.stop_running = False
        self.t = threading.Thread(target=self._animate)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_running = True
        self.t.join()
        # Clear the animation line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()
        
        if exc_type:
            # If your code crashed inside the 'with' block
            error(f"{self.message} Failed")
        else:
            success(f"{self.message} Complete")

    def _animate(self):
        # Braille pattern for smooth spinning
        chars = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        col_code = COLORS.get(self.color, COLORS['cyan'])
        rst = COLORS['reset']
        
        while not self.stop_running:
            sys.stdout.write(f'\r{col_code}{next(chars)} {self.message}...{rst}')
            sys.stdout.flush()
            time.sleep(0.1)

def inspect(obj):
    """
    Developer Tool: Inspects an object and lists its public methods and properties.
    Great for debugging libraries without documentation.
    """
    obj_type = type(obj).__name__
    print(f"\n{COLORS['magenta']}┌── INSPECT: {obj_type.upper()} {COLORS['reset']}{'─'*30}")
    
    # Separate attributes into Methods and Properties
    methods = []
    props = []
    
    for attr in dir(obj):
        if not attr.startswith('_'): # Skip private/magic methods
            try:
                val = getattr(obj, attr)
                if callable(val):
                    methods.append(attr)
                else:
                    props.append(f"{attr} = {str(val)[:40]}") # Truncate long values
            except:
                continue

    if props:
        print(f"{COLORS['yellow']}│ [Properties]{COLORS['reset']}")
        for p in props: print(f"│   • {p}")
        
    if methods:
        print(f"{COLORS['blue']}│ [Methods]{COLORS['reset']}")
        # Group methods in rows of 3 to save space
        for i in range(0, len(methods), 3):
            row = methods[i:i+3]
            print(f"│   • {', '.join(row)}")
            
    print(f"{COLORS['magenta']}└{'─'*45}{COLORS['reset']}\n")

    # ==========================================
# FEATURE: EASY FILE MANAGER
# ==========================================

def save(filename, data, mode="append"):
    """
    Saves data to a file easily.
    
    Args:
        filename (str): "data.txt", "log.csv", etc.
        data (any): The string or object to save.
        mode (str): "append" (add to bottom) or "overwrite" (replace file).
    """
    try:
        # Auto-convert non-strings to string
        text = str(data)
        
        # Decide write mode
        w_mode = 'w' if mode == 'overwrite' else 'a'
        
        with open(filename, w_mode, encoding='utf-8') as f:
            # Smart Newline: Only add newline if appending and text doesn't have one
            if w_mode == 'a' and not text.endswith('\n'):
                f.write(text + '\n')
            else:
                f.write(text)
                
        # Optional: Silent success or visible? Let's keep it silent for utility
        # but you can uncomment below to see confirmations:
        # success(f"Saved to {filename}")
        
    except Exception as e:
        error(f"Save Failed: {e}")

def read(filename, line=None):
    """
    Fetches data from a file.
    
    Args:
        filename (str): File path.
        line (int): Optional. If provided, returns ONLY that line number (1-based).
                    If None, returns the whole text.
    Returns:
        str or None (if error)
    """
    if not os.path.exists(filename):
        error(f"File not found: {filename}")
        return None

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # 1. Fetch All
            if line is None:
                return f.read().strip()
            
            # 2. Fetch Specific Line (1-based index)
            lines = f.readlines()
            if 1 <= line <= len(lines):
                return lines[line - 1].strip()
            else:
                warn(f"Line {line} does not exist (File has {len(lines)} lines).")
                return None
                
    except Exception as e:
        error(f"Read Failed: {e}")
        return None

def lines(filename):
    """
    Fetches file content as a clean LIST of strings.
    """
    if not os.path.exists(filename):
        return []
        
    with open(filename, 'r', encoding='utf-8') as f:
        # generic generator that strips newlines automatically
        return [l.strip() for l in f.readlines()]

def edit(filename, line_num, new_data):
    """
    Modifies a specific line in a file without deleting the rest.
    
    Args:
        line_num (int): 1-based line number.
        new_data (str): The new text to put there.
    """
    current_data = lines(filename)
    
    if not current_data:
        error(f"Cannot edit {filename} (File empty or missing)")
        return

    # Check Bounds (1-based conversion)
    index = line_num - 1
    if 0 <= index < len(current_data):
        current_data[index] = str(new_data)
        
        # Write everything back
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_data) + '\n')
        success(f"Line {line_num} updated.")
    else:
        error(f"Line {line_num} out of bounds.")
        # ==========================================
# FEATURE: ADVANCED DATA FILES (CSV/JSON)
# ==========================================

def read_csv(filename):
    """
    Reads a CSV file and returns it as a list of dictionaries.
    Great for Data Science.
    
    Example:
        data = say.read_csv("users.csv")
        print(data[0]['username'])
    """
    if not os.path.exists(filename):
        error(f"CSV not found: {filename}")
        return []

    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            # DictReader automatically uses the first row as keys
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        error(f"Failed to read CSV: {e}")
        return []

def save_csv(filename, data, headers=None):
    """
    Saves a list of dictionaries (or lists) to a CSV file.
    
    Args:
        data (list): List of dicts [{'name':'Ali'}, {'name':'Sim'}]
        headers (list): Optional. If None, auto-detected from keys.
    """
    if not data:
        warn("No data to save to CSV.")
        return

    try:
        mode = 'w'
        # Detect if data is List of Dicts or List of Lists
        is_dict = isinstance(data[0], dict)
        
        with open(filename, mode=mode, newline='', encoding='utf-8') as f:
            if is_dict:
                # Auto-detect headers if not provided
                if not headers:
                    headers = list(data[0].keys())
                
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            else:
                # Standard list of lists
                writer = csv.writer(f)
                if headers: writer.writerow(headers)
                writer.writerows(data)
                
        success(f"CSV Saved: {filename}")
        
    except Exception as e:
        error(f"Failed to save CSV: {e}")

def read_json(filename):
    """
    Loads a JSON file directly into a Python Dictionary/List.
    """
    if not os.path.exists(filename):
        return {} # Return empty dict if file doesn't exist
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json_lib.load(f)
    except Exception as e:
        error(f"JSON Error: {e}")
        return {}

def save_json(filename, data):
    """
    Saves a Python Dictionary/List to a JSON file with pretty formatting.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json_lib.dump(data, f, indent=4)
        success(f"JSON Saved: {filename}")
    except Exception as e:
        error(f"Failed to save JSON: {e}")

        # ==========================================
# FEATURE: SYSTEM & NETWORK
# ==========================================

def run(command, silent=False):
    """
    Executes a shell command and returns the output.
    
    Args:
        command (str): E.g., "git status" or "ls -la"
        silent (bool): If True, suppresses output and only returns result.
    
    Returns:
        str: The standard output of the command.
    """
    try:
        # Run command and capture output
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        output = result.stdout.strip()
        
        if not silent and output:
            print(output)
            
        return output
        
    except subprocess.CalledProcessError as e:
        # Command failed (non-zero exit code)
        err_msg = e.stderr.strip()
        if not silent:
            error(f"Command Failed: {command}\n{err_msg}")
        return None

def fetch(url, as_json=False):
    """
    Downloads data from a URL (GET request).
    Zero dependencies (uses standard urllib).
    
    Args:
        url (str): The web address.
        as_json (bool): If True, parses the result as a Dictionary.
    
    Returns:
        str or dict: The fetched data.
    """
    try:
        if not url.startswith('http'):
            url = 'https://' + url
            
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            
            if as_json:
                return json_lib.loads(data)
            return data
            
    except Exception as e:
        error(f"Fetch Error ({url}): {e}")
        return None

def walker(iterable, desc="Processing"):
    """
    A wrapper to automatically show a progress bar for any loop.
    Like 'tqdm' but built-in.
    
    Usage:
        for item in say.walker(my_list):
            ...
    """
    total = len(iterable)
    
    # Hide cursor
    sys.stdout.write('\033[?25l')
    
    for i, item in enumerate(iterable):
        yield item
        # Update progress bar (reusing your existing logic)
        progress(i + 1, total, prefix=desc)
        
    # Show cursor again
    sys.stdout.write('\033[?25h')

    # ==========================================
# FEATURE: STRING MASTERY
# ==========================================

def typewriter(text, speed=0.03, color=None, end='\n'):
    """
    Prints text one character at a time like a retro computer.
    """
    col = COLORS.get(color, '')
    rst = COLORS['reset']
    
    sys.stdout.write(col)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # Randomize speed slightly for realism
        time.sleep(speed + random.uniform(-0.01, 0.01))
    
    sys.stdout.write(rst + end)

def slug(text):
    """
    Converts 'My Cool Project v1.0' -> 'my-cool-project-v1-0'
    Essential for creating safe filenames or URLs.
    """
    # Lowercase and remove weird chars
    text = text.lower().strip()
    # Replace non-alphanumeric with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    return text.strip('-')

def cipher(text, shift=13):
    """
    Encrypts/Decrypts text using a Caesar Shift (ROT13 style).
    Good for hiding basic secrets in files.
    """
    result = ""
    for char in text:
        if char.isalpha():
            # Determine ASCII offset (65 for A, 97 for a)
            start = 65 if char.isupper() else 97
            # Shift character
            result += chr((ord(char) - start + shift) % 26 + start)
        else:
            result += char
    return result

def extract(text, mode="email", start=None, end=None):
    """
    The Ultimate Extractor.
    
    Modes:
    - "email" : Finds all emails.
    - "url"   : Finds all http links.
    - "number": Finds all integers/floats.
    - "between": Finds text between 'start' and 'end' markers.
    """
    if mode == "email":
        return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    
    elif mode == "url":
        return re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
    
    elif mode == "number":
        # Finds integers and floats
        return [float(x) if '.' in x else int(x) for x in re.findall(r'-?\d+\.?\d*', text)]
    
    elif mode == "between":
        if not start or not end:
            return []
        # Escape markers just in case
        pattern = re.escape(start) + "(.*?)" + re.escape(end)
        return re.findall(pattern, text, re.DOTALL)
    
    return []

def random_id(length=8):
    """Generates a random ID (e.g., 'A7x9_b2Z')."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ==========================================
# FEATURE: PRO UTILITIES
# ==========================================

def retry(retries=3, delay=1, backoff=2):
    """
    Decorator: Automatically retries a function if it crashes.
    
    Args:
        retries (int): How many times to try.
        delay (int): Initial seconds to wait before retrying.
        backoff (int): Multiplier for delay (1s -> 2s -> 4s).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mdelay = delay
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1: # Last attempt
                        raise e
                    
                    warn(f"Error: {e}. Retrying in {mdelay}s... ({i+1}/{retries})")
                    time.sleep(mdelay)
                    mdelay *= backoff
        return wrapper
    return decorator

def ago(dt_obj):
    """
    Converts a datetime object to 'Time Ago' string.
    Example: '5 minutes ago', 'Just now', '2 days ago'.
    """
    if not isinstance(dt_obj, datetime.datetime):
        return "Unknown"
        
    now = datetime.datetime.now()
    diff = now - dt_obj
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)} mins ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"

def load_env(filename=".env"):
    """
    Loads variables from a .env file into os.environ.
    Format: KEY=VALUE
    """
    if not os.path.exists(filename):
        return False
        
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            # Remove quotes if present
            value = value.strip("'").strip('"')
            os.environ[key.strip()] = value
            
    return True

def gradient(text, start_hex, end_hex):
    """
    Prints text in a beautiful color gradient (RGB).
    
    Args:
        text (str): The text to print.
        start_hex (str): Hex color code (e.g., "#FF0000").
        end_hex (str): Hex color code (e.g., "#0000FF").
    """
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    r1, g1, b1 = hex_to_rgb(start_hex)
    r2, g2, b2 = hex_to_rgb(end_hex)
    
    length = len(text)
    if length == 0: return

    for i, char in enumerate(text):
        # Calculate intermediate color
        r = int(r1 + (r2 - r1) * i / length)
        g = int(g1 + (g2 - g1) * i / length)
        b = int(b1 + (b2 - b1) * i / length)
        
        # ANSI RGB code: \033[38;2;R;G;Bm
        sys.stdout.write(f"\033[38;2;{r};{g};{b}m{char}")
        
    sys.stdout.write(COLORS['reset'] + "\n")

    # ==========================================
# FEATURE: SMART LOOPS (Flow Control)
# ==========================================

def repeat(times, func, *args, **kwargs):
    """
    Executes a function N times.
    Usage: say.repeat(5, print, "Hello")
    """
    results = []
    for i in range(times):
        try:
            res = func(*args, **kwargs)
            results.append(res)
        except Exception as e:
            error(f"Iteration {i+1} Failed: {e}")
    return results

def every(seconds, func, stop_condition=None):
    """
    Runs a function every X seconds in the background (Non-blocking).
    Great for auto-saving or checking server status.
    
    Args:
        stop_condition (lambda): If returns True, the loop stops.
    """
    def loop_wrapper():
        while True:
            if stop_condition and stop_condition():
                break
            try:
                func()
            except Exception as e:
                warn(f"Background Task Error: {e}")
            time.sleep(seconds)
            
    t = threading.Thread(target=loop_wrapper, daemon=True)
    t.start()
    return t

def until(condition_func, timeout=10, interval=0.5):
    """
    Waits/Loops until a condition becomes True (Poller).
    Essential for 'Waiting for Internet' or 'Waiting for File'.
    
    Returns True if condition met, False if timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    
    warn(f"Wait timed out after {timeout}s")
    return False

def chunks(data, size=10):
    """
    Smart Iterator: Splits a massive list into smaller batches.
    Enterprise Usage: "Process 1000 users, 50 at a time."
    
    Usage:
        for batch in say.chunks(all_users, 50):
            db.insert(batch)
    """
    for i in range(0, len(data), size):
        yield data[i:i + size]

# ==========================================
# FEATURE: ENTERPRISE SAFETY
# ==========================================

def safe_run(func, default=None, show_error=True):
    """
    Runs a function. If it crashes, it returns 'default' instead of killing the app.
    Usage: value = say.safe_run(risky_math_function, default=0)
    """
    try:
        return func()
    except Exception as e:
        if show_error:
            warn(f"Safe Run Caught Error: {e}")
        return default

def mask(text, visible_chars=2):
    """
    Hides sensitive data (API Keys, Passwords) for logging.
    "supersecretpassword" -> "su*****************"
    """
    text = str(text)
    if len(text) <= visible_chars * 2:
        return "*" * len(text)
    return text[:visible_chars] + "*" * (len(text) - (visible_chars*2)) + text[-visible_chars:]

def throttle(seconds=1):
    """
    Decorator: Ensures a function cannot be called too often.
    Prevents API rate limiting or button spamming.
    """
    def decorator(func):
        last_called = [0]
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_called[0] >= seconds:
                last_called[0] = now
                return func(*args, **kwargs)
            else:
                # Optionally warn: say("Throttled", color="yellow")
                return None
        return wrapper
    return decorator

