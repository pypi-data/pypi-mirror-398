import re
import json
import dns.resolver
import dns.reversename
from stealth_chopper.validation import is_private_ip

def load_tld_mapping(file_path):
    with open(file_path, 'r') as file:
        tld_data = json.load(file)
    tld_to_country = {}
    for entry in tld_data:
        country = entry["country"]
        for tld in entry["tlds"]:
            tld_to_country[tld] = country
    
    return tld_to_country

def extract_base_domain(dns_query, tld_to_country):
    cleaned_query = re.sub(r',+', '.', dns_query)
    cleaned_query = re.sub(r'[^\w\.-]', '', cleaned_query)
    match = re.match(r"(?:[a-zA-Z0-9-]+\.)+([a-zA-Z0-9-]+\.[a-zA-Z]+)", cleaned_query)
    
    if match:
        domain = match.group(1)
        parts = domain.split('.')
        base_domain = '.'.join(parts[-2:])
        tld = '.' + parts[-1]
        country = tld_to_country.get(tld, 'Unknown')
        
        return base_domain, country
    else:
        return cleaned_query, 'Unknown'

def ip_to_domain(ip, ip_domain_cache):
    if ip in ip_domain_cache:
        return ip_domain_cache[ip]
    
    if is_private_ip(ip):
        ip_domain_cache[ip] = None
        return None
    try:
        rev_name = dns.reversename.from_address(ip)
        domain = dns.resolver.resolve(rev_name, "PTR")[0].to_text()
        ip_domain_cache[ip] = domain
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout) as e:
        ip_domain_cache[ip] = ip
    except Exception as e:
        ip_domain_cache[ip] = ip 
    return ip_domain_cache[ip]