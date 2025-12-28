import json
import os
from .say import json_print, success, error, warn, box

# ==========================================
# PART 1: ULTRA-SIMPLE TEXT FILES
# ==========================================

def write_file(filename, content):
    """
    Saves text to a file in one line.
    Usage: storage.write_file("notes.txt", "Hello World")
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(content))
        success(f"Saved to '{filename}'")
    except Exception as e:
        error(f"Could not write file: {e}")

def read_file(filename):
    """
    Reads text from a file in one line.
    Usage: content = storage.read_file("notes.txt")
    """
    if not os.path.exists(filename):
        error(f"File '{filename}' not found.")
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        error(f"Could not read file: {e}")
        return None

def append_file(filename, content):
    """Adds text to the end of a file without deleting existing content."""
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(str(content) + "\n")
        success(f"Appended to '{filename}'")
    except Exception as e:
        error(f"Could not append: {e}")

# ==========================================
# PART 2: THE "MINI DATABASE" (JSON Wrapper)
# ==========================================

class MiniDB:
    """
    A lightweight JSON database.
    
    Usage:
        db = MiniDB("users.json")
        db.set("username", "ali")  # Auto-saves
        print(db.get("username"))
    """
    
    def __init__(self, filename="database.json"):
        self.filename = filename
        self.data = self._load()

    def _load(self):
        """Internal: Loads data from disk."""
        if not os.path.exists(self.filename):
            return {}
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except:
            warn(f"Database '{self.filename}' was corrupted or empty. Starting fresh.")
            return {}

    def _save(self):
        """Internal: Saves data to disk."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            error(f"Database Save Failed: {e}")

    # --- PUBLIC API ---

    def set(self, key, value):
        """Saves a key-value pair."""
        self.data[key] = value
        self._save()
        # success(f"Saved key '{key}'") # Optional: uncomment if you want noise

    def get(self, key, default=None):
        """Fetches a value."""
        return self.data.get(key, default)

    def delete(self, key):
        """Removes a key."""
        if key in self.data:
            del self.data[key]
            self._save()
            success(f"Deleted '{key}'")
        else:
            warn(f"Key '{key}' not found.")

    def push(self, list_name, item):
        """
        Adds an item to a list inside the database.
        Great for logs or user records.
        """
        if list_name not in self.data:
            self.data[list_name] = []
        
        if not isinstance(self.data[list_name], list):
            error(f"Key '{list_name}' is not a list!")
            return

        self.data[list_name].append(item)
        self._save()

    def search(self, query):
        """
        Finds keys or values containing the query text.
        Returns a dictionary of matches.
        """
        query = str(query).lower()
        results = {}
        for k, v in self.data.items():
            if query in str(k).lower() or query in str(v).lower():
                results[k] = v
        return results

    def view(self):
        """Prints the whole database nicely."""
        box(self.data, title=f"DB: {self.filename}", color="cyan")

    def wipe(self):
        """DANGER: Deletes everything."""
        self.data = {}
        self._save()
        warn("Database wiped clean.")