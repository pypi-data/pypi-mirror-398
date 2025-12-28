import hashlib
import base64
import time
import json
import socket
import random
import string
import functools
import os
import re
import threading
from collections import deque
import functools
import time
# ==========================================
# SECTION 1: ALGORITHMS & LOGIC (CLASSIC)
# ==========================================

def is_prime(n):
    """Checks if a number is Prime."""
    if n <= 1: return False
    if n <= 3: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def fibonacci_sequence(n):
    """Returns a list of the first n terms of Fibonacci."""
    if n <= 0: return []
    if n == 1: return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq

def bubble_sort(arr):
    """Educational implementation of Bubble Sort."""
    n = len(arr)
    # Optimize: stop if no swaps occurred
    for i in range(n):
        swapped = False
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr

def binary_search(arr, target):
    """
    Standard Binary Search. 
    Returns index of target, or -1 if not found.
    NOTE: Array must be sorted first!
    """
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] < target:
            low = mid + 1
        elif arr[mid] > target:
            high = mid - 1
        else:
            return mid
    return -1

# ==========================================
# SECTION 2: CRYPTOGRAPHY & ENCODING
# ==========================================

def hash_string_md5(text):
    """Returns MD5 hash of a string (32 chars)."""
    return hashlib.md5(text.encode()).hexdigest()

def hash_string_sha256(text):
    """Returns SHA256 hash (more secure than MD5)."""
    return hashlib.sha256(text.encode()).hexdigest()

def base64_encode(text):
    """Encodes string to Base64."""
    return base64.b64encode(text.encode()).decode()

def base64_decode(encoded_text):
    """Decodes Base64 string back to normal."""
    return base64.b64decode(encoded_text.encode()).decode()

def caesar_cipher(text, shift):
    """
    Encrypts text by shifting letters.
    A classic CS homework problem.
    """
    result = ""
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            # (Current Char - Start + Shift) % 26 + Start
            result += chr((ord(char) - start + shift) % 26 + start)
        else:
            result += char
    return result

def generate_strong_password(length=12):
    """Generates a secure password with mix of chars."""
    if length < 4: length = 4
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one of each type
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    # Fill the rest
    for _ in range(length - 4):
        password.append(random.choice(chars))
    random.shuffle(password)
    return "".join(password)

# ==========================================
# SECTION 3: BITWISE MAGIC (SYSTEMS)
# ==========================================

def get_bit(number, position):
    """Returns the bit (0 or 1) at position i."""
    return (number >> position) & 1

def set_bit(number, position):
    """Sets the bit at position i to 1."""
    return number | (1 << position)

def clear_bit(number, position):
    """Sets the bit at position i to 0."""
    return number & ~(1 << position)

def toggle_bit(number, position):
    """Flips the bit at position i."""
    return number ^ (1 << position)

def count_set_bits(n):
    """Counts how many 1s are in the binary representation."""
    return bin(n).count('1')

# ==========================================
# SECTION 4: NETWORKING BASICS
# ==========================================

def get_local_ip():
    """Returns the local IP address of the machine."""
    try:
        # Connect to a dummy external server to see which interface is used
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_hostname():
    """Returns the computer's name."""
    return socket.gethostname()

# ==========================================
# SECTION 5: PERFORMANCE (BIG O ANALYSIS)
# ==========================================

def execution_timer(func):
    """
    Decorator to print how long a function takes to run.
    Usage:
        @execution_timer
        def my_slow_function(): ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[{func.__name__}] executed in {end_time - start_time:.6f} seconds")
        return result
    return wrapper

# ==========================================
# SECTION 6: FILE SYSTEM HELPERS
# ==========================================

def read_json(filepath):
    """Reads a JSON file and returns a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} not found.")
    with open(filepath, 'r') as f:
        return json.load(f)

def write_json(filepath, data):
    """Writes a dictionary to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def file_size(filepath):
    """Returns human-readable file size (KB, MB, GB)."""
    if not os.path.exists(filepath):
        return "File not found"
    
    size_bytes = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

# ==========================================
# SECTION 7: DATA STRUCTURES (CLASSES)
# ==========================================

class Stack:
    """LIFO (Last In, First Out) Data Structure."""
    def __init__(self):
        self.items = []
    def push(self, item): self.items.append(item)
    def pop(self): return self.items.pop() if not self.is_empty() else None
    def peek(self): return self.items[-1] if not self.is_empty() else None
    def is_empty(self): return len(self.items) == 0
    def size(self): return len(self.items)
    def __str__(self): return str(self.items)

class Queue:
    """FIFO (First In, First Out) Data Structure."""
    def __init__(self):
        self.items = []
    def enqueue(self, item): self.items.insert(0, item)
    def dequeue(self): return self.items.pop() if not self.is_empty() else None
    def is_empty(self): return len(self.items) == 0
    def size(self): return len(self.items)
    def __str__(self): return str(self.items)



    # ==========================================
# SECTION 8: REGEX HELPERS (PATTERNS)
# ==========================================

def is_valid_email(email):
    """Checks if a string is a valid email format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def is_valid_url(url):
    """Checks if a string is a valid URL (http/https)."""
    pattern = r"^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
    return bool(re.match(pattern, url))

def extract_numbers(text):
    """Returns a list of all numbers found in a text string."""
    return [int(n) for n in re.findall(r'\d+', text)]

def extract_emails(text):
    """Finds all email addresses in a large text block."""
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return re.findall(pattern, text)

def sanitize_filename(filename):
    """Removes illegal characters from a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# ==========================================
# SECTION 9: CONCURRENCY (THREADING)
# ==========================================

def run_in_background(func, *args):
    """
    Runs a function in a separate thread immediately.
    Useful for students learning non-blocking code.
    """
    t = threading.Thread(target=func, args=args)
    t.daemon = True # Kills thread if main program exits
    t.start()
    return t

def parallel_map(func, items):
    """
    Applies func to items in parallel using threads.
    (Simple implementation for IO-bound tasks).
    """
    threads = []
    results = [None] * len(items)

    def worker(index, item):
        results[index] = func(item)

    for i, item in enumerate(items):
        t = threading.Thread(target=worker, args=(i, item))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    
    return results

# ==========================================
# SECTION 10: GRAPH ALGORITHMS
# ==========================================

class Graph:
    """A simple Adjacency List Graph for BFS/DFS demos."""
    def __init__(self):
        self.adj_list = {}

    def add_edge(self, u, v, bidirectional=True):
        """Adds a connection between node u and node v."""
        if u not in self.adj_list: self.adj_list[u] = []
        if v not in self.adj_list: self.adj_list[v] = []
        
        self.adj_list[u].append(v)
        if bidirectional:
            self.adj_list[v].append(u)

    def bfs(self, start_node):
        """Breadth-First Search (Layer by Layer). Returns visited order."""
        visited = set()
        queue = deque([start_node])
        result = []

        visited.add(start_node)
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return result

    def dfs(self, start_node):
        """Depth-First Search (Deepest first). Returns visited order."""
        visited = set()
        result = []

        def _dfs_recursive(node):
            visited.add(node)
            result.append(node)
            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    _dfs_recursive(neighbor)
        
        _dfs_recursive(start_node)
        return result
    

# ==========================================
# SECTION 11: PRODUCTION DECORATORS
# ==========================================

def retry(retries=3, delay=2):
    """
    Decorator: If the function fails, it tries again.
    Usage:
        @retry(retries=3, delay=1)
        def connect_to_db(): ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    print(f"[Warning] Function '{func.__name__}' failed (Attempt {attempt}/{retries}). Error: {e}")
                    if attempt == retries:
                        print(f"[Error] '{func.__name__}' failed permanently.")
                        raise e  # Re-raise the error after final attempt
                    time.sleep(delay)
        return wrapper
    return decorator

def benchmark(func):
    """
    Decorator: Measures memory and time usage of a function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"PERFORMANCE: '{func.__name__}' took {end - start:.5f} seconds.")
        return result
    return wrapper