import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import os
import shutil
import subprocess
import sys


def check_openssl():
    if not shutil.which("openssl"):
        print("Error: 'openssl' command not found.")
        sys.exit(1)


def generate_keys(selector, output_dir="."):
    priv_filename = os.path.join(output_dir, f"{selector}.private")
    print(f"[*] Generating key for '{selector}'...")

    try:
        subprocess.run(
            ["openssl", "genrsa", "-out", priv_filename, "2048"],
            check=True,
            stderr=subprocess.DEVNULL,
        )
        result = subprocess.run(
            ["openssl", "rsa", "-in", priv_filename, "-pubout", "-outform", "PEM"],
            check=True,
            capture_output=True,
            text=True,
        )
        raw_key = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"OpenSSL Error: {e}")
        sys.exit(1)

    lines = raw_key.splitlines()
    clean_key = "".join(line for line in lines if "-----" not in line)
    print(f"✅ Saved private key to: {priv_filename}")
    return clean_key


def generate_and_print(selector, domain):
    check_openssl()
    pub_key = generate_keys(selector)
    record = f"v=DKIM1; k=rsa; p={pub_key}"

    print("\n" + "=" * 60)
    print("DNS TXT RECORD TO ADD")
    print("=" * 60)
    print(f"Host:   {selector}._domainkey")
    print(f"Value:  {record}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate DKIM keys.")
    parser.add_argument("selector", help="DKIM selector")
    parser.add_argument("--domain", default="yourdomain.com")
    args = parser.parse_args()
    generate_and_print(args.selector, args.domain)


if __name__ == "__main__":
    main()
