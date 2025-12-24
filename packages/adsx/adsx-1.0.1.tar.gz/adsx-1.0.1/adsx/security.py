import hmac, sys
from getpass import getpass

PASSWORD = "1616"

def check():
    p = getpass("Enter password: ")
    if not hmac.compare_digest(p, PASSWORD):
        print("❌ Access denied")
        sys.exit(1)
