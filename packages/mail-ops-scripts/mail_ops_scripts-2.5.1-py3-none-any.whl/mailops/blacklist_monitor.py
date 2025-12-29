import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# mailops/blacklist_monitor.py
import argparse
import ipaddress
import json
import urllib.request

from . import ui  # Import the new UI module

# Common RBLs
RBL_PROVIDERS = [
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "b.barracudacentral.org",
    "dnsbl.sorbs.net",
    "ips.backscatterer.org",
]


def resolve_domain(domain):
    print(f"[*] Resolving IP for: {domain}...", end=" ", flush=True)
    url = f"https://dns.google/resolve?name={domain}&type=A"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        if "Answer" in data:
            for answer in data["Answer"]:
                if answer["type"] == 1:
                    ip = answer["data"]
                    print(f"Found {ip}")
                    return ip
        print("\n[!] Error: No A record found.")
        return None
    except Exception as e:
        print(f"\n[!] DNS Lookup Error: {e}")
        return None


def check_rbl(ip_address, rbl_domain):
    try:
        reversed_ip = ".".join(reversed(ip_address.split(".")))
        query = f"{reversed_ip}.{rbl_domain}"
        url = f"https://dns.google/resolve?name={query}&type=A"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        if "Answer" in data:
            return data["Answer"][0]["data"]
        return None
    except Exception as e:
        return f"Error: {e}"


def run_check(target_input):
    """Orchestrates the check logic so other scripts can call it."""
    target_ip = None
    try:
        ipaddress.ip_address(target_input)
        target_ip = target_input
    except ValueError:
        target_ip = resolve_domain(target_input)
        if not target_ip:
            return

    ui.print_sub_header(f"Blacklist Status for: {target_ip}")
    print("-" * 60)
    print(f"{'RBL Provider':<30} | {'Status':<10}")
    print("-" * 60)

    issues = 0
    for rbl in RBL_PROVIDERS:
        res = check_rbl(target_ip, rbl)
        if res is None:
            print(f"{rbl:<30} | ✅ Clean")
        elif str(res).startswith("Error"):
            print(f"{rbl:<30} | ⚠️  {res}")
        else:
            print(f"{rbl:<30} | ❌ LISTED ({res})")
            issues += 1
    print("-" * 60)
    if issues == 0:
        ui.print_success("Great! This IP is not listed on the checked RBLs.")
    else:
        ui.print_warning(f"This IP is listed on {issues} blacklists.")


def main():
    parser = argparse.ArgumentParser(description="Check RBL status.")
    parser.add_argument("target", help="IP address or Domain")
    args = parser.parse_args()
    run_check(args.target)


if __name__ == "__main__":
    main()
