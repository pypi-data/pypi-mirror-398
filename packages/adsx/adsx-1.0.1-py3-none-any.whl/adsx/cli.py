from adsx.security import check
from adsx.runner import run_setup   # ✅ renamed

def run():
    print("🔐 ADSX Protected Installer")
    check()
    run_setup()   # ✅ now calls correct function
