import os
import sys
import json
import shutil
import subprocess

BASE_DIR = os.path.dirname(__file__)
PAYLOAD = os.path.join(BASE_DIR, "payload")

def run_setup():
    folder = input("Enter folder name: ").strip()
    if not folder:
        print("❌ Folder name required")
        sys.exit(1)

    # mkdir + cd
    os.makedirs(folder, exist_ok=True)
    os.chdir(folder)

    # create venv
    print("📦 Creating virtual environment...")
    subprocess.run(["python3", "-m", "venv", "source"], check=True)

    VENV_PY = os.path.abspath("source/bin/python")
    VENV_PIP = os.path.abspath("source/bin/pip")

    # copy files
    print("📁 Copying bot files...")
    for name in os.listdir(PAYLOAD):
        src = os.path.join(PAYLOAD, name)
        if os.path.isfile(src):
            shutil.copy(src, ".")

    # ask bot token BEFORE daemon
    values_path = os.path.join(os.getcwd(), "values.json")
    with open(values_path, "r") as f:
        config = json.load(f)

    if not config.get("bot_token"):
        token = input("Enter Telegram Bot Token: ").strip()
        if not token:
            print("❌ Bot token required")
            sys.exit(1)

        config["bot_token"] = token
        with open(values_path, "w") as f:
            json.dump(config, f, indent=2)

        print("✅ Bot token saved")

    # install requirements INTO VENV
    print("📥 Installing requirements...")
    subprocess.run([VENV_PIP, "install", "-r", "requirements.txt"], check=True)

    # ensure supercore exists
    SUPERCORE = shutil.which("supercore")
    if not SUPERCORE:
        print("❌ supercore not found. Install it first.")
        sys.exit(1)

    # run bots (THIS IS THE KEY)
    print("🚀 Starting userbot (teleuserbot)")
    subprocess.Popen([SUPERCORE, VENV_PY, "userbot.py"])

    print("🚀 Starting app")
    subprocess.Popen([SUPERCORE, VENV_PY, "app.py"])

    print("✅ Setup complete")
