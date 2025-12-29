import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# mailops/ui.py


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    """Prints a bold, colorful header section."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.RESET}")


def print_sub_header(text):
    """Prints a sub-header (e.g., for individual reports)."""
    print(f"\n{Colors.BOLD}--- {text} ---{Colors.RESET}")


def print_error(text):
    """Prints an error message in Red."""
    print(f"{Colors.RED}[!] Error: {text}{Colors.RESET}")


def print_warning(text):
    """Prints a warning in Yellow."""
    print(f"{Colors.YELLOW}[!] Warning: {text}{Colors.RESET}")


def print_success(text):
    """Prints a success message in Green."""
    print(f"{Colors.GREEN}[+] {text}{Colors.RESET}")


def print_info(text):
    """Prints a general info message in Blue."""
    print(f"{Colors.BLUE}[*] {text}{Colors.RESET}")
