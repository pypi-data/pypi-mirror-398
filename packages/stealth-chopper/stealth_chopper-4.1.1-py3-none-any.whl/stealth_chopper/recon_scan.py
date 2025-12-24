import subprocess
import re
import ipaddress
import time
import os

def get_subnet():
    iface = subprocess.getoutput("ip route get 1 | awk '{print $5; exit}'")
    cidr = subprocess.getoutput(f"ip addr show {iface} | grep 'inet ' | awk '{{print $2}}'").strip()
    network = ipaddress.ip_interface(cidr).network
    return str(network), iface

def perform_nmap_scan(subnet, retries=5, delay=5):
    unique_targets = {}

    for _ in range(retries):
        cmd = f"sudo arp-scan --localnet -t {delay*500}"
        result = subprocess.getoutput(cmd)
        for line in result.splitlines():
            match = re.search(
                r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f:]{17})\s+(.*)",
                line,
                re.I
            )
            if not match:
                continue

            ip, mac, vendor = match.groups()
            vendor = vendor.strip()
            first_byte = int(mac.split(":")[0], 16)
            is_random_mac = (first_byte & 2) != 0
            if is_random_mac or "unknown" in vendor.lower():
                vendor = "Unknown"
            if ip not in unique_targets or unique_targets[ip] == "Unknown":
                unique_targets[ip] = vendor

        print(f"Discovered {len(unique_targets)} unique hosts so far...")
        time.sleep(delay)
    target_dir = "src/stealth_chopper/assets"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    target_file = os.path.join(target_dir, "targets.txt")
    with open(target_file, "w") as f:
        for ip, vendor in unique_targets.items():
            f.write(f"{ip} ({vendor})\n")

    print(f"\nFinal unique targets saved to {target_file}")
    return unique_targets

def choose_target_by_index(targets):
    print("\nTargets:")
    for i, (ip, hostname) in enumerate(targets.items()):
        print(f"  {i}) \033[1;32m{ip}\033[0m -> {hostname}")

    while True:
        choice = input("\nEnter the target index number, or type 'add' to manually add a target: ").strip()

        if choice.lower() == 'add':
            ip = input("Enter the IP address: ").strip()
            hostname = input("Enter the hostname: ").strip()
            targets[ip] = hostname
            print(f"Added {ip} -> {hostname} to targets.")
            for i, (ip, hostname) in enumerate(targets.items()):
                 print(f"  {i}) \033[1;32m{ip}\033[0m -> {hostname}")
            continue
        if not choice.isdigit():
            print("Please enter a valid number or 'add'.")
            continue

        idx = int(choice)

        if idx < 0 or idx >= len(targets):
            print(f"Invalid index. Please choose a number between 0 and {len(targets)-1}, or type 'add' to add a target.")
            continue
        selected_ip = list(targets.keys())[idx]
        return selected_ip, targets[selected_ip]