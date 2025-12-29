import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# mailops/dmarc_parser.py
import csv
import gzip
import os
import socket
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime

from . import ui  # Import the new UI module

IP_CACHE: dict[str, str] = {}


def resolve_ip(ip_address):
    """Resolves IP to Hostname with caching."""
    if ip_address in IP_CACHE:
        return IP_CACHE[ip_address]

    try:
        socket.setdefaulttimeout(2)
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        IP_CACHE[ip_address] = hostname
        return hostname
    except Exception:
        result = "Unknown"
        IP_CACHE[ip_address] = result
        return result


def analyze_record(spf, dkim, disposition):
    """
    Determines the status and color based on DMARC results.
    Returns: (Action_String, Color_Code)
    """
    if spf == "pass" or dkim == "pass":
        return "OK", ui.Colors.GREEN

    if disposition in ["quarantine", "reject"]:
        return "BLOCKED (Spoofing)", ui.Colors.YELLOW

    return "INVESTIGATE", ui.Colors.RED


# --- Core Logic ---


def parse_dmarc_xml(file_path):
    tree = None
    filename = os.path.basename(file_path)
    records_data = []

    try:
        if file_path.endswith(".gz"):
            with gzip.open(file_path, "rb") as f:
                tree = ET.parse(f)
        elif file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, "r") as z:
                xml_files = [n for n in z.namelist() if n.lower().endswith(".xml")]
                if not xml_files:
                    return []
                with z.open(xml_files[0]) as f:
                    tree = ET.parse(f)
        else:
            tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        ui.print_error(f"Processing '{filename}': {e}")
        return []

    org_name = root.findtext(".//org_name") or "Unknown Org"

    date_range = root.find(".//date_range")
    if date_range is not None:
        begin_ts = int(date_range.findtext("begin", 0))
        end_ts = int(date_range.findtext("end", 0))
        begin_date = datetime.fromtimestamp(begin_ts).strftime("%Y-%m-%d")
        end_date = datetime.fromtimestamp(end_ts).strftime("%Y-%m-%d")
    else:
        begin_date = end_date = "Unknown"

    records = root.findall("record")
    if not records:
        return []

    for record in records:
        row = record.find("row")
        source_ip = row.findtext("source_ip")
        count = row.findtext("count")
        disposition = row.find(".//policy_evaluated/disposition").text

        spf = record.find(".//auth_results/spf/result")
        spf_res = spf.text if spf is not None else "none"

        dkim = record.find(".//auth_results/dkim/result")
        dkim_res = dkim.text if dkim is not None else "none"

        # Extract envelope_to field from identifiers section
        # Location: feedback/record/identifiers/envelope_to
        identifiers = record.find("identifiers")
        if identifiers is not None:
            envelope_to = identifiers.findtext("envelope_to") or "Unknown"
        else:
            envelope_to = "Unknown"

        hostname = resolve_ip(source_ip)
        status_msg, status_color = analyze_record(spf_res, dkim_res, disposition)

        records_data.append(
            {
                "org_name": org_name,
                "date": begin_date,
                "source_ip": source_ip,
                "hostname": hostname,
                "envelope_to": envelope_to,
                "count": count,
                "spf": spf_res,
                "dkim": dkim_res,
                "disposition": disposition,
                "status_msg": status_msg,
                "status_color": status_color,
                "file": filename,
            }
        )

    return records_data


def print_to_console(all_data):
    if not all_data:
        ui.print_warning("No records found.")
        return

    current_file = None
    header_fmt = "{:<20} | {:<20} | {:<30} | {:<5} | {:<6} | {:<6} | {:<15}"
    row_fmt = "{:<20} | {:<20} | {:<30} | {:<5} | {:<6} | {:<6} | {:<15}"

    for row in all_data:
        if row["file"] != current_file:
            current_file = row["file"]
            ui.print_sub_header(f"Report: {row['org_name']} ({row['date']})")
            print("-" * 130)
            print(
                ui.Colors.HEADER
                + header_fmt.format(
                    "Source IP", "Envelope To", "Hostname", "Cnt", "SPF", "DKIM", "Analysis"
                )
                + ui.Colors.RESET
            )
            print("-" * 130)

        host_display = (
            (row["hostname"][:27] + "..")
            if len(row["hostname"]) > 29
            else row["hostname"]
        )
        
        envelope_display = (
            (row["envelope_to"][:17] + "..")
            if len(row["envelope_to"]) > 19
            else row["envelope_to"]
        )

        line = row_fmt.format(
            row["source_ip"],
            envelope_display,
            host_display,
            row["count"],
            row["spf"],
            row["dkim"],
            row["status_msg"],
        )
        print(row["status_color"] + line + ui.Colors.RESET)


def save_to_csv(all_data, output_file):
    if not all_data:
        return

    clean_data = [{k: v for k, v in r.items() if k != "status_color"} for r in all_data]
    headers = [
        "org_name",
        "date",
        "source_ip",
        "hostname",
        "envelope_to",
        "count",
        "spf",
        "dkim",
        "disposition",
        "status_msg",
        "file",
    ]

    try:
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(clean_data)
        ui.print_success(f"Exported to {output_file}")
    except Exception as e:
        ui.print_error(f"CSV Error: {e}")
