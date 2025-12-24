import os, shutil, subprocess, sys

BASE = os.path.dirname(__file__)
PAYLOAD = os.path.join(BASE, "payload")

def run_setup():   # ✅ renamed (VERY IMPORTANT)
    folder = input("Enter folder name: ").strip()
    if not folder:
        print("❌ Folder name required")
        sys.exit(1)

    os.makedirs(folder, exist_ok=True)
    os.chdir(folder)

    print("📦 Creating venv")
    subprocess.run(["python3", "-m", "venv", "source"], check=True)

    pip = os.path.join("source", "bin", "pip")
    python = os.path.join("source", "bin", "python")

    print("📁 Copying bot files")
    for f in os.listdir(PAYLOAD):
        shutil.copy(os.path.join(PAYLOAD, f), ".")

    print("📥 Installing requirements")
    subprocess.run([pip, "install", "-r", "requirements.txt"], check=True)

    print("🚀 Starting userbot (teleuserbot)")
    subprocess.Popen(["supercore", python, "userbot.py"])

    print("🚀 Starting app")
    subprocess.Popen(["supercore", python, "app.py"])

    print("✅ Setup complete")
