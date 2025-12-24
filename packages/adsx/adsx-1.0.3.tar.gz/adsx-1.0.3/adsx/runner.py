import os
import shutil
import subprocess
import sys
import json

BASE_DIR = os.path.dirname(__file__)
PAYLOAD = os.path.join(BASE_DIR, "payload")

def run_setup():
    folder = input("Enter folder name: ").strip()
    if not folder:
        print("❌ Folder name required")
        sys.exit(1)

    os.makedirs(folder, exist_ok=True)
    os.chdir(folder)

    print("📦 Creating virtual environment...")
    subprocess.run(["python3", "-m", "venv", "source"], check=True)

    pip = os.path.join("source", "bin", "pip")
    python = os.path.join("source", "bin", "python")

    print("📁 Copying bot files...")
    for name in os.listdir(PAYLOAD):
        src = os.path.join(PAYLOAD, name)
        if not os.path.isfile(src):
            continue
        shutil.copy(src, ".")

    # 🔑 ASK BOT TOKEN HERE (NOT IN BOT)
    values_path = os.path.join(os.getcwd(), "values.json")
    with open(values_path, "r") as f:
        config = json.load(f)

    if not config.get("bot_token"):
        bot_token = input("Enter Telegram Bot Token: ").strip()
        if not bot_token:
            print("❌ Bot token required")
            sys.exit(1)

        config["bot_token"] = bot_token
        with open(values_path, "w") as f:
            json.dump(config, f, indent=2)

        print("✅ Bot token saved")

    print("📥 Installing requirements...")
    subprocess.run([pip, "install", "-r", "requirements.txt"], check=True)

    print("🚀 Starting userbot (teleuserbot)")
    subprocess.Popen(["supercore", python, "userbot.py"])

    print("🚀 Starting app")
    subprocess.Popen(["supercore", python, "app.py"])

    print("✅ Setup complete")
