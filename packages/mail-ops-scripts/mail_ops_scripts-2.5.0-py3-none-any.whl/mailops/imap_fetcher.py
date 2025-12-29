import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import email
import getpass
import imaplib
import os
import sys
from email.header import decode_header

from . import ui  # Integrate with your new UI system


def clean_filename(filename):
    """Sanitizes filenames to prevent directory traversal issues."""
    if not filename:
        return None
    # Keep only safe characters
    return "".join(c for c in filename if c.isalnum() or c in "._-")


def get_safe_date(msg):
    """Extracts a safe YYYY-MM-DD date from the email."""
    date_str = msg.get("Date")
    if date_str:
        try:
            date_obj = email.utils.parsedate_to_datetime(date_str)
            return date_obj.strftime("%Y-%m-%d")
        except:
            pass
    return "unknown_date"


def safe_decode(value):
    """Safely decodes bytes to string."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)


def decode_header_safe(header_val):
    """Decodes email headers (Subject, Filename) securely."""
    if not header_val:
        return None
    try:
        decoded_list = decode_header(header_val)
        result = []
        for content, encoding in decoded_list:
            if isinstance(content, bytes):
                if encoding:
                    try:
                        result.append(content.decode(encoding, errors="ignore"))
                    except LookupError:
                        # Fallback for unknown encodings
                        result.append(content.decode("utf-8", errors="ignore"))
                else:
                    result.append(content.decode("utf-8", errors="ignore"))
            else:
                result.append(str(content))
        return "".join(result)
    except Exception:
        return str(header_val)


def fetch_reports(username, password, server, folder="INBOX"):
    ui.print_info(f"Connecting to {server}...")

    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(username, password)
    except Exception as e:
        ui.print_error(f"Login Failed: {e}")
        return

    ui.print_info("Login successful. Searching for DMARC reports...")
    mail.select(folder)

    # Search for DMARC specific subjects
    search_criteria = '(OR SUBJECT "Report Domain" SUBJECT "DMARC Aggregate Report")'
    status, messages = mail.search(None, search_criteria)

    if status != "OK" or not messages[0]:
        ui.print_warning("No DMARC reports found in INBOX.")
        return

    email_ids = messages[0].split()
    ui.print_info(f"Found {len(email_ids)} potential report emails. Processing...")

    count = 0

    for e_id in email_ids:
        try:
            # Fetch the email body
            res, msg_data = mail.fetch(e_id, "(BODY[])")
            if res != "OK":
                continue

            raw_email = None

            # Standard IMAP extraction (Tuple usually contains the body)
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    raw_email = response_part[1]
                    break

            if raw_email is None:
                continue

            # Parse email object
            msg = email.message_from_bytes(raw_email)
            folder_date = get_safe_date(msg)
            subject = decode_header_safe(msg.get("Subject", "Unknown Subject"))

            # Walk through email parts to find attachments
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue

                # Check explicitly for attachments
                content_disposition = part.get("Content-Disposition", "")
                is_attachment = "attachment" in content_disposition.lower()

                filename = decode_header_safe(part.get_filename())
                content_type = part.get_content_type()

                # LOGIC: It must look like a DMARC report (XML, GZIP, ZIP)
                valid_extension = filename and filename.lower().endswith(
                    (".xml", ".gz", ".zip")
                )
                valid_mime = any(x in content_type for x in ["gzip", "zip", "xml"])

                if is_attachment or valid_extension or valid_mime:
                    # If no filename, generate one from subject
                    if not filename:
                        ext = ".xml"
                        if "gzip" in content_type:
                            ext = ".gz"
                        elif "zip" in content_type:
                            ext = ".zip"

                        safe_subj = clean_filename(subject)
                        filename = f"dmarc_report_{safe_subj}{ext}"

                    filename = clean_filename(filename)

                    if filename:
                        # Save Logic
                        save_dir = os.path.join("dmarc_reports", folder_date)
                        os.makedirs(save_dir, exist_ok=True)
                        filepath = os.path.join(save_dir, filename)

                        if not os.path.exists(filepath):
                            payload = part.get_payload(decode=True)
                            if payload:
                                with open(filepath, "wb") as f:
                                    f.write(payload)
                                ui.print_success(f"Saved: {folder_date}/{filename}")
                                count += 1

        except Exception as e:
            ui.print_error(f"Processing email ID {e_id}: {e}")
            continue

    mail.close()
    mail.logout()
    print("-" * 60)
    ui.print_success(f"Download complete. Saved {count} new reports.")
    ui.print_info(f"Location: {os.path.abspath('dmarc_reports')}")


def main():
    parser = argparse.ArgumentParser(description="Download DMARC reports from IMAP.")
    parser.add_argument("--email", required=True, help="Your email address")
    parser.add_argument("--server", default="imap.mail.me.com", help="IMAP Server")

    args = parser.parse_args()

    print(f"Enter IMAP Password for {args.email}")
    try:
        password = getpass.getpass("> ")
    except KeyboardInterrupt:
        sys.exit(0)

    fetch_reports(args.email, password, args.server)


if __name__ == "__main__":
    main()
