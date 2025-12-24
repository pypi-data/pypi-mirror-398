import sys
from getpass import getpass
import hmac

PASSWORD = "1616"

def check_password():
    print("🔐 ADSX Protected Installer")
    p = getpass("Enter password: ")
    if not hmac.compare_digest(p, PASSWORD):
        print("❌ Wrong password")
        sys.exit(1)
