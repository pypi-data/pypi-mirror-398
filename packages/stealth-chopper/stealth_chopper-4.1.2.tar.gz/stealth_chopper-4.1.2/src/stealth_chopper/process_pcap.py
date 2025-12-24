#!/usr/bin/env python3
import sys
import argparse
from scapy.all import rdpcap, IP, DNS, DNSQR, Ether
import socket
import re
from colorama import init, Fore
from tabulate import tabulate
from datetime import datetime
from stealth_chopper.extraction import extract_base_domain, load_tld_mapping
from stealth_chopper.validation import is_valid_domain
from mac_vendor_lookup import MacLookup
import os
init(autoreset=True)

def format_timestamp(ts):
    return datetime.fromtimestamp(int(float(ts))).strftime("%Y-%m-%d %H:%M:%S")

def parse_time_filter(time_str):
    if not time_str:
        return None
    time_str = time_str.strip() if len(time_str) != 19 else time_str
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", time_str):
        return datetime.strptime(time_str, "%Y-%m-%d")
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", time_str):
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    elif re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", time_str) or re.match(r"[\^\$\.\*\+\?\[\]\\]", time_str):
        return time_str
    else:
        print(Fore.RED + f"[!] Invalid time format: {time_str}. Use YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, or HH:MM[:SS]")

def process_pcap(pcap_file, filter_ip=None, filter_url=None, filter_country=None, filter_time=None,
                 search_string=None, filter_mac=None, filter_vendor=None, filter_hostname=None):
    venv_root = sys.prefix 
    venv_name = os.path.basename(venv_root)
    lib_path = os.path.join(venv_root, 'lib')
    python_version = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    site_packages = os.path.join(lib_path, python_version, 'site-packages')
    relative_path = os.path.join(venv_name, *site_packages.split(os.sep)[3:])
    tld_file_path = os.path.join(relative_path, 'stealth_chopper', 'assets', 'tld.txt')
    if not os.path.isfile(tld_file_path):
        print(Fore.RED + f"[!] TLD file not found at: {tld_file_path}")
        sys.exit(1)
    tld_to_country = load_tld_mapping(tld_file_path)
    visited_domains_by_ip = {}
    visited_time_by_ip = {}
    mac_by_ip = {}
    hostnames_by_ip = {}
    vendors_by_ip = {}
    mac_lookup = MacLookup()
    time_filter_dt = parse_time_filter(filter_time)
    try:
        packets = rdpcap(pcap_file)
    except FileNotFoundError:
        print(Fore.RED + f"[!] File not found: {pcap_file}")
        return

    print(Fore.CYAN + f"[+] Total packets: {len(packets)}\n")

    for pkt in packets:
        if IP in pkt:
            src = pkt[IP].src
            
            if Ether in pkt:
                mac = pkt[Ether].src
                mac_by_ip[src] = mac
                try:
                    vendor = mac_lookup.lookup(mac)
                except Exception:
                    vendor = "Unknown"
                vendors_by_ip[src] = vendor
            else:
                mac_by_ip.setdefault(src, "Unknown")
                vendors_by_ip.setdefault(src, "Unknown")

            if src not in hostnames_by_ip:
                try:
                    hostnames_by_ip[src] = socket.gethostbyaddr(src)[0]
                except Exception:
                    hostnames_by_ip[src] = "Unknown"

            # Apply filters if set
            if filter_ip and not re.match(filter_ip, src):
                continue
            if filter_mac and not re.match(filter_mac, mac_by_ip.get(src, "")):
                continue
            if filter_vendor and filter_vendor.lower() not in vendors_by_ip.get(src, "").lower():
                continue
            if filter_hostname and filter_hostname.lower() not in hostnames_by_ip.get(src, "").lower():
                continue

            if DNS in pkt and pkt.haslayer(DNSQR):
                pkt_time = datetime.fromtimestamp(float(pkt.time))
                
                # Time-based filtering
                if time_filter_dt:
                    if isinstance(time_filter_dt, datetime):
                        if time_filter_dt.hour == 0 and time_filter_dt.minute == 0 and time_filter_dt.second == 0:
                            if pkt_time.date() != time_filter_dt.date():
                                continue
                        else:
                            if pkt_time.replace(microsecond=0) != time_filter_dt.replace(microsecond=0):
                                continue
                    elif isinstance(time_filter_dt, str):
                        pkt_time_str = pkt_time.strftime("%H:%M:%S")
                        if not (pkt_time_str.startswith(time_filter_dt) or re.match(time_filter_dt, pkt_time_str)):
                            continue

                dns_qr = pkt[DNSQR]
                dns_query = dns_qr.qname.decode()
                base_domain, _ = extract_base_domain(dns_query, tld_to_country)
                
                if not is_valid_domain(base_domain):
                    continue
                if search_string and not re.search(search_string, base_domain, re.IGNORECASE):
                    continue

                # Extract TLD and country code
                tld = "." + base_domain.split('.')[-1]
                country = tld_to_country.get(tld, "Unknown")
                if filter_country and filter_country.upper() != country.upper():
                    continue

                # Store domain visits and times
                if src not in visited_domains_by_ip:
                    visited_domains_by_ip[src] = set()
                    visited_time_by_ip[src] = {}

                visited_domains_by_ip[src].add(base_domain)
                if base_domain not in visited_time_by_ip[src]:
                    visited_time_by_ip[src][base_domain] = format_timestamp(pkt.time)

    table_data = []
    for ip, domains in visited_domains_by_ip.items():
        mac = mac_by_ip.get(ip, "Unknown")
        vendor = vendors_by_ip.get(ip, "Unknown")
        hostname = hostnames_by_ip.get(ip, "Unknown")

        for domain in domains:
            domain = domain.rstrip('.')
            time_visited = visited_time_by_ip[ip].get(domain, "")
            tld = "." + domain.split('.')[-1]
            country = tld_to_country.get(tld, "Unknown")

            row = [
                Fore.GREEN + ip,
                Fore.CYAN + hostname,
                Fore.MAGENTA + vendor,
                Fore.YELLOW + mac,
                Fore.YELLOW + domain,
                Fore.GREEN + "Yes",
                Fore.WHITE + country
            ]
            if time_visited:
                row.append(Fore.WHITE + time_visited)
            table_data.append(row)

    headers = [
        Fore.YELLOW + "Source IP",
        Fore.YELLOW + "Hostname",
        Fore.YELLOW + "Vendor",
        Fore.YELLOW + "MAC Address",
        Fore.YELLOW + "Visited Domain",
        Fore.YELLOW + "Visited",
        Fore.YELLOW + "Country"
    ]
    if table_data and len(table_data[0]) == 8:
        headers.append(Fore.YELLOW + "Time Visited")

    print("\n" + Fore.GREEN + "[+] Visit Status:")
    print(tabulate(table_data, headers, tablefmt="fancy_grid", stralign="center"))

def parse_arguments():
    parser = argparse.ArgumentParser(description="PCAP Analyzer: Filter by IP, URL, Country, Time, MAC, Vendor, Hostname")
    parser.add_argument("-f", "--file", required=True, help="Path to the PCAP file.")
    parser.add_argument("-s", "--search", help="Search for a specific URL or domain (regex allowed).")
    parser.add_argument("-c", "--country", help="Filter by country code (TLD based).")
    parser.add_argument("-i", "--ip", help="Filter packets by source IP (regex allowed).")
    parser.add_argument("-t", "--time", help="Filter by visit time (YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, or HH:MM:SS).")
    parser.add_argument("-m", "--mac", help="Filter by MAC address (regex allowed).")
    parser.add_argument("-v", "--vendor", help="Filter by Vendor name (case-insensitive).")
    parser.add_argument("-H", "--hostname", help="Filter by Hostname (case-insensitive).")
    return parser.parse_args()

def print_usage():
    print(Fore.CYAN + "Usage:")
    print(Fore.YELLOW + "\tstealth-chopper-pcap -f <pcap_file> -s [filter_url] -i [filter_ip] -c [filter_country] -t [time] -m [mac] -v [vendor] -H [hostname]\n")
    print(Fore.CYAN + "Examples:")
    print(Fore.YELLOW + "\tstealth-chopper-pcap -f *.pcap -s '.*linkedin.com' -i '192.168.1.121' -c 'US' -t '2025-12-07 13:20:30' -m 'xx:xx:xx:xx:xx:xx' -v 'mobile' -H 'router'")
def main():
    if len(sys.argv) == 1:
        print_usage()
        sys.exit(1)

    args = parse_arguments()
    process_pcap(
        args.file,
        filter_ip=args.ip,
        filter_url=args.search,
        filter_country=args.country,
        filter_time=args.time,
        search_string=args.search,
        filter_mac=args.mac,
        filter_vendor=args.vendor,
        filter_hostname=args.hostname
    )
if __name__ == '__main__':
    main()