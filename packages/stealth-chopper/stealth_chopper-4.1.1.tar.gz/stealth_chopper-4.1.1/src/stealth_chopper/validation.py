import sys
import os
import ipaddress
import psutil
import shutil
import subprocess
import re
from colorama import Fore, init

def is_valid_ipv4(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except Exception:
        return False
def is_private_ip(ip):
    private_ips = [
        ipaddress.IPv4Network("10.0.0.0/8"),
        ipaddress.IPv4Network("172.16.0.0/12"),
        ipaddress.IPv4Network("192.168.0.0/16"),
    ]
    
    ip_obj = ipaddress.ip_address(ip)
    
    for net in private_ips:
        if ip_obj in net:
            return True
    return False

def is_valid_iface(iface):
    return iface in psutil.net_if_addrs().keys()

def check_dependencies():
    """Ensure required tools exist in PATH."""
    required = ["ettercap", "etterfilter", "bettercap", "wireshark"]
    missing = [tool for tool in required if not shutil.which(tool)]
    if missing:
        print(Fore.RED + f"[!] Missing dependencies: {', '.join(missing)}")
        sys.exit(1)

def is_valid_domain(domain):
    domain = domain.rstrip('.')
    if any(x in domain for x in ['.local', '_tcp', '_udp', '.arpa']):
        return False
    if re.match(r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}", domain):
        return True
    return False

def ensure_url_file():
    # Path to the url_file.txt within the project (if needed)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "src", "stealth_chopper", "assets")
    url_file = os.path.join(assets_dir, "url_file.txt")

    needs_creation = False

    # Check if url_file.txt exists and is valid
    if not os.path.isfile(url_file):
        needs_creation = True
    else:
        try:
            with open(url_file, "r") as f:
                contents = f.read().strip()
                if not contents:
                    needs_creation = True
        except Exception:
            needs_creation = True

    # If url_file.txt is missing or empty, run common_url.py to regenerate it
    if needs_creation:
        print(Fore.YELLOW + "[*] No valid url_file.txt found. Running common_url.py...")

        # Path to the installed version of common_url.py in site-packages
        common_url_path = os.path.join(sys.prefix, "lib", "python3.13", "site-packages", "stealth_chopper", "common_url.py")

        # Ensure common_url.py exists in the installed package location
        if not os.path.isfile(common_url_path):
            print(Fore.RED + f"[!] common_url.py not found at {common_url_path}")
            sys.exit(1)

        try:
            # Run common_url.py using the current Python interpreter
            result = subprocess.run(
                [sys.executable, common_url_path],  # Use sys.executable to ensure we're using the correct Python
                check=True,
                capture_output=True,
                text=True
            )
            print(Fore.GREEN + "[+] common_url.py executed successfully.")
            if result.stdout.strip():
                print(Fore.CYAN + f"[*] common_url.py output:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"[!] Failed to execute common_url.py: {e.stderr}")
            sys.exit(1)

    return url_file
