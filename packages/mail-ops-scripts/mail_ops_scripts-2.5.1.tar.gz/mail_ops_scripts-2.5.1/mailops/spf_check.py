import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# mailops/spf_check.py
import argparse
import json
import urllib.request

from . import ui  # Import the new UI module


def fetch_spf_record(domain):
    """
    Fetches the SPF record for a domain using Google's DNS-over-HTTPS API.
    """
    ui.print_info(f"Fetching SPF record for '{domain}'...")

    url = f"https://dns.google/resolve?name={domain}&type=TXT"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

        if "Answer" not in data:
            ui.print_warning(f"No TXT records found for {domain}.")
            return None

        spf_records = []
        for answer in data["Answer"]:
            txt_data = answer["data"].strip('"').replace('" "', "")
            if txt_data.startswith("v=spf1"):
                spf_records.append(txt_data)

        if not spf_records:
            ui.print_warning(f"No SPF record found for {domain}.")
            return None

        if len(spf_records) > 1:
            ui.print_warning(f"Multiple SPF records found! This is invalid.")
            for r in spf_records:
                print(f"    - {r}")
            return spf_records[0]

        return spf_records[0]

    except Exception as e:
        ui.print_error(f"Fetching DNS: {e}")
        return None


def analyze_spf(spf_string):
    """
    Analyzes the SPF string for syntax errors and security best practices.
    """
    ui.print_sub_header(f"Analysis for: {spf_string}")
    issues = []
    warnings = []

    # 1. Basic Syntax
    if not spf_string.startswith("v=spf1"):
        issues.append("Record does not start with 'v=spf1'")

    # 2. Lookup Counting (Approximation)
    lookup_mechanisms = ["include:", "a:", "mx:", "ptr:", "exists:", "redirect="]
    tokens = spf_string.split()
    lookup_count = 0

    for token in tokens:
        for mech in lookup_mechanisms:
            if token.startswith(mech):
                lookup_count += 1
        if token == "a" or token == "mx":
            lookup_count += 1

    print(f"[*] DNS Lookup Count (Approx): {lookup_count}/10")
    if lookup_count > 10:
        issues.append(f"Too many DNS lookups ({lookup_count}). Limit is 10 (RFC 7208).")

    # 3. Security Checks
    if "+all" in tokens:
        issues.append(
            "Usage of '+all' allows the entire internet to spoof your domain."
        )
    elif "?all" in tokens:
        warnings.append("Usage of '?all' (Neutral) provides no protection.")
    elif not (
        tokens[-1].endswith("-all")
        or tokens[-1].endswith("~all")
        or "redirect=" in tokens[-1]
    ):
        issues.append("Record does not end with a strict policy ('-all' or '~all').")

    if "ptr" in spf_string:
        warnings.append("The 'ptr' mechanism is deprecated and should not be used.")

    # Report
    if not issues and not warnings:
        ui.print_success("Status: Valid & Secure")
    else:
        if issues:
            print(f"{ui.Colors.RED}❌ Critical Issues:{ui.Colors.RESET}")
            for i in issues:
                print(f"   - {i}")
        if warnings:
            print(f"{ui.Colors.YELLOW}⚠️  Warnings:{ui.Colors.RESET}")
            for w in warnings:
                print(f"   - {w}")
