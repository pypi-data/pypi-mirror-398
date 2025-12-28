import socket
import hashlib
import requests
import time
import threading
from .say import say, progress, success, warn, error
import platform
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor
import re

# ==========================================
# 1. NETWORK RECONNAISSANCE
# ==========================================

class PortScanner:
    """
    Scans a target IP to find open ports (doors).
    """
    def __init__(self):
        self.open_ports = []

    def scan(self, target_ip, ports=[21, 22, 80, 443, 3306, 8080]):
        """
        ports: List of ports to check.
        21=FTP, 22=SSH, 80=HTTP, 3306=MySQL
        """
        say(f"--- Scanning Target: {target_ip} ---", color="cyan")
        self.open_ports = []
        
        for p in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1) # Wait 1 second max
            
            result = sock.connect_ex((target_ip, p))
            if result == 0:
                success(f"Port {p} is OPEN")
                self.open_ports.append(p)
            else:
                # pass # Don't print closed ports to keep output clean
                pass
            sock.close()
            
        return self.open_ports

# ==========================================
# 2. CRYPTOGRAPHY & PASSWORDS
# ==========================================

class Crypto:
    @staticmethod
    def hash_text(text, algo="sha256"):
        """Converts text to a non-reversible hash."""
        text_bytes = text.encode('utf-8')
        if algo == "md5":
            return hashlib.md5(text_bytes).hexdigest()
        elif algo == "sha256":
            return hashlib.sha256(text_bytes).hexdigest()
    
    @staticmethod
    def caesar_cipher(text, shift=3):
        """Simple encryption used by Julius Caesar."""
        result = ""
        for char in text:
            if char.isalpha():
                shift_amount = 65 if char.isupper() else 97
                # Mathematics of rotation
                result += chr((ord(char) - shift_amount + shift) % 26 + shift_amount)
            else:
                result += char
        return result

class BruteForce:
    """
    Demonstrates how weak passwords are cracked.
    """
    def __init__(self):
        self.found = None

    def dictionary_attack(self, target_hash, wordlist):
        """
        Tries to find the password that matches the target_hash.
        target_hash: The encrypted password found in a database.
        wordlist: A list of common passwords (e.g. ['password', '123456'])
        """
        say(f"--- Starting Dictionary Attack ---", color="yellow")
        
        for i, word in enumerate(wordlist):
            # 1. Hash the guess
            guess_hash = Crypto.hash_text(word, "sha256")
            
            # 2. Compare
            if guess_hash == target_hash:
                success(f"CRACKED! Password is: '{word}'")
                return word
            
            # Visuals
            if i % 10 == 0:
                print(f"\rTrying: {word}...", end="")
                time.sleep(0.01) # Slow down slightly for effect
        
        error("\nPassword not found in dictionary.")
        return None

# ==========================================
# 3. WEB VULNERABILITY SCANNER
# ==========================================

class WebScanner:
    """
    Basic checks for website security.
    """
    def __init__(self, url):
        self.url = url

    def scan_headers(self):
        """Checks if the server reveals too much info."""
        try:
            r = requests.get(self.url)
            headers = r.headers
            say("\n--- Server Headers ---", color="magenta")
            
            server = headers.get("Server")
            if server:
                warn(f"Server Software Revealed: {server}")
            else:
                success("Server header is hidden (Good!)")
                
            x_frame = headers.get("X-Frame-Options")
            if not x_frame:
                error("Missing 'X-Frame-Options' (Vulnerable to Clickjacking)")
            else:
                success("Clickjacking protection enabled.")
                
        except Exception as e:
            error(f"Could not connect: {e}")

    def check_sql_injection(self):
        """
        Checks if a URL parameter is vulnerable to SQL Injection.
        Adds a single quote (') to the URL and checks for errors.
        """
        test_url = f"{self.url}'" # Malicious payload
        try:
            r = requests.get(test_url)
            if "SQL syntax" in r.text or "mysql_fetch" in r.text:
                error(f"VULNERABLE: {self.url} seems vulnerable to SQL Injection!")
            else:
                success(f"Safe: No obvious SQL errors found on {self.url}")
        except:
            pass

        # ==========================================
# 4. NETWORK MAPPING (Find Live Hosts)
# ==========================================

class NetworkMapper:
    """
    Scans a local network to find active devices (Ping Sweep).
    OS-Independent (Auto-detects Windows/Linux/Mac).
    """
    def __init__(self):
        self.os_type = platform.system().lower()
        # Windows uses '-n', Linux/Mac uses '-c' for ping count
        self.ping_flag = '-n' if 'windows' in self.os_type else '-c'

    def ping(self, ip):
        """Returns True if host is up, False if down."""
        command = ['ping', self.ping_flag, '1', ip]
        try:
            # Run ping silently (stdout to DEVNULL)
            response = subprocess.call(
                command, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            return response == 0
        except:
            return False

    def sweep(self, subnet):
        """
        Scans a subnet (e.g., '192.168.1') for all 254 hosts.
        Uses threading for speed.
        """
        say(f"--- Sweeping Network: {subnet}.x ---", color="cyan")
        active_hosts = []

        def check_host(i):
            ip = f"{subnet}.{i}"
            if self.ping(ip):
                success(f"Host Found: {ip}")
                active_hosts.append(ip)

        # Scan 1 to 254 simultaneously
        with ThreadPoolExecutor(max_workers=50) as executor:
            for i in range(1, 255):
                executor.submit(check_host, i)
        
        return active_hosts

# ==========================================
# 5. WEB ENUMERATION (Directory Busting)
# ==========================================

class DirBuster:
    """
    Finds hidden admin panels or backup files on a website.
    """
    def __init__(self, url):
        self.url = url if url.endswith('/') else url + '/'
        self.common_paths = [
            "admin", "login", "dashboard", "config", "backup", 
            "robots.txt", ".env", "phpinfo.php", "users"
        ]

    def scan(self, custom_list=None):
        say(f"--- Busting Directories on {self.url} ---", color="magenta")
        paths = custom_list if custom_list else self.common_paths
        
        found = []
        for path in paths:
            target = self.url + path
            try:
                r = requests.get(target, timeout=2)
                if r.status_code == 200:
                    success(f"FOUND: {target} (200 OK)")
                    found.append(target)
                elif r.status_code == 403:
                    warn(f"FORBIDDEN: {target} (403 - Interesting!)")
                elif r.status_code == 404:
                    pass # Not found
                else:
                    info(f"Checking {target} -> {r.status_code}")
            except:
                pass
        return found

# ==========================================
# 6. SYSTEM RECON (Malware Simulation)
# ==========================================

class SystemRecon:
    """
    Demonstrates what information hackers gather first when they compromise a system.
    """
    @staticmethod
    def get_info():
        say("--- System Fingerprint ---", color="yellow")
        
        # 1. OS Details
        uname = platform.uname()
        print(f"System:   {uname.system}")
        print(f"Node:     {uname.node}")
        print(f"Release:  {uname.release}")
        print(f"Version:  {uname.version}")
        print(f"Machine:  {uname.machine}")
        print(f"Processor:{uname.processor}")
        
        # 2. User Info
        try:
            print(f"User:     {os.getlogin()}")
        except:
            pass # Sometimes fails in certain IDEs
            
        # 3. Network Interfaces (Basic)
        print(f"Hostname: {socket.gethostname()}")
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            print(f"Local IP: {local_ip}")
        except:
            pass

# ==========================================
# 7. STEGANOGRAPHY (Hidden Data)
# ==========================================

class Stegano:
    """
    Hides text inside other text using Zero Width Characters.
    This allows 'invisible' communication.
    """
    # Zero width space characters
    ZERO_WIDTH = {'0': '\u200b', '1': '\u200c'} 
    
    @staticmethod
    def hide(secret_message, public_message):
        """Embeds secret binary into public text."""
        # Convert secret to binary
        binary = ''.join(format(ord(i), '08b') for i in secret_message)
        
        # Replace 0/1 with invisible chars
        hidden_string = ''
        for bit in binary:
            hidden_string += Stegano.ZERO_WIDTH[bit]
            
        return public_message + hidden_string

    @staticmethod
    def reveal(stego_text):
        """Extracts secret from text."""
        binary = ''
        for char in stego_text:
            if char == '\u200b':
                binary += '0'
            elif char == '\u200c':
                binary += '1'
        
        if not binary: return "No hidden message found."
        
        # Convert binary back to text
        message = ""
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            message += chr(int(byte, 2))
        return message

# ... (Keep previous classes) ...

# ==========================================
# 8. PHISHING DEFENSE & ANALYSIS
# ==========================================

class PhishDetector:
    """
    Analyzes a URL to determine if it looks suspicious.
    Used to teach students common indicators of phishing.
    """
    def __init__(self):
        self.suspicious_keywords = ['login', 'verify', 'update', 'account', 'secure', 'banking']

    def analyze(self, url):
        say(f"--- Analyzing URL: {url} ---", color="magenta")
        score = 0
        reasons = []

        # 1. Check for IP Address usage (e.g., http://192.168.1.1/login)
        # Legitimate sites usually use domain names.
        ip_pattern = r"http[s]?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        if re.search(ip_pattern, url):
            score += 40
            reasons.append("Uses IP address instead of domain name")

        # 2. Check for the '@' symbol
        # Browsers ignore everything before '@', so 'http://google.com@evil.com' goes to evil.com
        if '@' in url:
            score += 30
            reasons.append("Contains '@' symbol (Redirection trick)")

        # 3. Check for Suspicious Length
        if len(url) > 75:
            score += 10
            reasons.append("URL is suspiciously long")

        # 4. Check for multiple 'http' tokens
        # e.g., http://google.com-redirect.com/login?q=http://...
        if url.count("http") > 1:
            score += 20
            reasons.append("Multiple 'http' tokens found (Redirect chain?)")

        # 5. Check keywords in subdomain
        # e.g. http://paypal.update-security.com (This is NOT paypal.com)
        for word in self.suspicious_keywords:
            if word in url:
                # Simple check; real analysis requires TLD parsing
                reasons.append(f"Contains sensitive keyword: '{word}'")
                score += 5

        # Verdict
        print(f"Phishing Score: {score}/100")
        if reasons:
            warn("Risk Factors Found:")
            for r in reasons:
                print(f" - {r}")
        
        if score > 50:
            error("VERDICT: HIGHLY SUSPICIOUS")
        elif score > 20:
            warn("VERDICT: POTENTIALLY UNSAFE")
        else:
            success("VERDICT: LIKELY SAFE")

class Typosquatter:
    """
    Demonstrates how attackers register 'look-alike' domains.
    Visualizes Homograph Attacks.
    """
    def __init__(self):
        self.swaps = {
            'o': '0',
            'l': '1',
            'i': '1',
            'e': '3',
            'a': '4',
            's': '5',
            't': '7',
            'b': '8',
            'g': 'q',
            'm': 'rn'
        }

    def generate(self, domain):
        """Generates common phishing variations of a domain name."""
        say(f"--- Generating Phishing Variations for: {domain} ---", color="cyan")
        variations = []
        
        # 1. Visual Swaps (Homoglyphs)
        fake = ""
        for char in domain:
            fake += self.swaps.get(char, char)
        if fake != domain:
            variations.append(f"{fake} (Visual Spoof)")

        # 2. TLD Swap
        if ".com" in domain:
            variations.append(f"{domain.replace('.com', '.net')} (TLD Swap)")
            variations.append(f"{domain.replace('.com', '.co')} (TLD Drop)")

        # 3. Hyphenation trick
        # facebook.com -> face-book.com
        if len(domain) > 6 and '-' not in domain:
            mid = len(domain) // 2
            variations.append(f"{domain[:mid]}-{domain[mid:]} (Hyphenation)")

        for v in variations:
            print(f" - {v}")
            
        return variations