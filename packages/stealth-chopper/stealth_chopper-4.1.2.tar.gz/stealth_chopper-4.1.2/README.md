# StealthChopper 

> **Aggressive Sniffer & MITM Launcher**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/%7C%20Linux-green?logo=linux)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-4.1-orange)

---

This Python-based tool allows network monitoring professionals and security enthusiasts to quickly launch **Ettercap**, **Bettercap**, and **Wireshark** for packet sniffing and MITM analysis on a selected target IP and interface. It also analyzes PCAP files, filtering packets by URL and/or IP, and displays which domains were visited by a specific IP along with timestamps and visit status.

## Features

1. **Custom Packet Filter Generator**: Automatically generates and compiles an Ettercap filter file to drop traffic from all IPs except the target. 
2.  **Wireshark Auto-Launch with Filters**: Opens Wireshark with a live display filter for the target IP and optionally filtered domains from `url_file.txt`.   
3.  **PCAP Analyzer**: This tool allows you to analyze PCAP files and filter packets based on a specific URL and/or IP address. It shows which domains were visited by a particular IP, including timestamps and visit status.

## Installation (with pip)

```bash
curl -LO https://raw.githubusercontent.com/cyb2rS2c/StealthChopper/refs/heads/main/setup_pip.sh
chmod +x setup_pip.sh; source ./setup_pip.sh

```


## Project Tree
```bash
.
├── 192.168.0.121_filtered_activity.pcap
├── assets
├── ├── targets.txt
│   ├── tld.txt
│   └── url_file.txt
├── excluded_ips.ef
├── excluded_ips.efc
├── LICENSE
├── README.md
├── requirements.txt
├── setup.sh
├── setup_pip.sh (optional using pip)
└── src
    ├── animation.py
    ├── common_url.py
    ├── extraction.py
    ├── listenOnSomeOne.py
    ├── recon_scan.py
    ├── process_pcap.py
    └── validation.py
```

## Installation (GitHub)

1. Clone the repository:

```bash
git clone https://github.com/cyb2rS2c/StealthChopper.git
cd StealthChopper
```

2. Install the required Python dependencies and run the program (**Interactive**):

```bash
chmod +x setup.sh;source ./setup.sh
```

## Usage

Run the script as root, specifying the target IP and interface as arguments:

### Option1 (Manually)
```bash
sudo python3 src/listenOnSomeOne.py <target_ip> <interface>
```
### Option2 (Wizard)

```bash
sudo python3 src/listenOnSomeOne.py --scan
```
### Option3
```bash
sudo python3 src/listenOnSomeOne.py --interactive
```

**Example:**

```bash
sudo python3 listenOnSomeOne.py 192.168.1.121 wlan0
```
- `<target_ip>`: The single IPv4 address you want to target.
- `<interface>`: The network interface to use (e.g., `eth0`, `wlan0`).

**The script will:**

    1-Validate your IP and interface input.
    2-Ensure url_file.txt exists (generates it via common_url.py if missing).
    3-Create a custom filter file excluding all other IPs.
    4-Compile the filter file for Ettercap.
    5-Launch Ettercap, Bettercap, and Wireshark in separate terminal sessions.
    6-Apply a Wireshark filter for target IP and optionally domains from url_file.txt.
    Tip: Press Ctrl+C in the main terminal to exit gracefully.

# PCAP Analyzer

## Usage
```
python3 src/process_pcap.py -f <pcap_file> -s [filter_url] -i [filter_ip] -c [country] -t [HH:MM:SS | YYYY-MM-DD | YYYY-MM-DD HH:MM:SS]
```


**Example:**

### 1. Check if a user has visited `linkedin.com` from a specific IP address:

```bash
# Check if the user with IP "192.168.1.121" has visited "linkedin.com"
# If so, it will show the visit time and other useful details.
python3 src/process_pcap.py -f 192.168.0.121_filtered_activity.pcap -s ".*linkedin.com" -i "192.168.1.121"

# Alternatively, you can search for just "linkedin" (without the full domain).
# This will match any domain containing "linkedin" like linkedin.com etc.
python3 src/process_pcap.py -f 192.168.0.121_filtered_activity.pcap -s "linkedin" -i "192.168.1.121"
```
### 2. Check all websites visited by a user with a specific IP address:
```bash
# This will display all the domains the user has queried in the PCAP.
python3 src/process_pcap.py -f 192.168.0.121_filtered_activity.pcap -i "192.168.1.121"
```
### 3. Check all users who have visited linkedin.com:
```bash
# This will display all users who have visited any domain containing "linkedin".
# It shows the visit status, including the time of visit.
python3 src/process_pcap.py -f 192.168.0.121_filtered_activity.pcap -s "linkedin"
```
### 4. Check users by country:
```bash
# This will display all users who have visited any domain containing "linkedin".
# It filters results by country, showing only visits from users in the specified country (e.g., US).
python3 src/process_pcap.py -f 192.168.0.121_filtered_activity.pcap -s "linkedin" -c "US"
```
### 5. Check users by specific visit time:
```
# This will display all users who visited any domain containing "linkedin" on a specific date and time (e.g., "2025-12-07 13:20:30").
python3 src/process_pcap.py -f 192.168.0.121_filtered_activity.pcap -s "linkedin" -t "2025-12-07 13:20:30"
```

### 6. New Features / Changes

The following columns have been added and can now be filtered:

***Vendor*** - the manufacturer of the device, based on the MAC address.

***MAC Address*** - the device’s network interface identifier.

***Hostname*** - the resolved name of the device.
```bash
# Example
python3 src/process_pcap.py -f 192.168.0.121_filtered_activity.pcap -v "Liteon" -H "router" -m "00:00:00:00:00:00"
```

**Tip:** Use Regex for domain filtering as shown in the example above if you don't want to enter the full FQDN.

### 6. Help
#### To get help on how to use the script, you can view the usage instructions with the following commands:

```bash
python3 src/listenOnSomeOne.py -h
``` 
#### For PCAP analyzer type:
```bash
python3 src/process_pcap.py -h
#OR
python3 src/process_pcap.py 
```

## Screenshots
Navigate to the following link to explore the images from the PyPI project. - [**Screenshots**](https://github.com/cyb2rS2c/StealthChopper/blob/main/images/pip/pip_images.md)

## Educational Purposes

This project is intended for educational purposes only. The code demonstrates how to interact with system commands and network interfaces via Python. Do not use this toolkit for unauthorized or illegal network activities. Always obtain proper authorization before testing network security.

## Author
cyb2rS2c - [GitHub Profile](https://github.com/cyb2rS2c)

# License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/cyb2rS2c/StealthChopper/blob/main/LICENSE) file for details.

## Disclaimer!

This code is provided "as-is" without any warranty. The author is not responsible for any misuse or damage caused by the use of this software. Always practice responsible security testing.
