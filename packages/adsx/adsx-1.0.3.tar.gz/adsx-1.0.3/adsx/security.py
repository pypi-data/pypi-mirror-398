import hmac
import sys
from getpass import getpass

PASSWORD = "1616"

def check_password():
    print("🔐 ADSX Protected Installer")
    p = getpass("Enter password: ")

    if not hmac.compare_digest(p, PASSWORD):
        print("❌ Access denied")
        sys.exit(1)
