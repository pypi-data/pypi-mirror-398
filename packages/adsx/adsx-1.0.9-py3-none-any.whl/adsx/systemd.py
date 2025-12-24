import os
import getpass
from pathlib import Path

SERVICE_PATH = "/etc/systemd/system/adsx.service"

SERVICE_TEMPLATE = """[Unit]
Description=AdsX Telegram Bot
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={home}
ExecStart={exec} fg
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

def install_service():
    user = getpass.getuser()
    home = str(Path.home())
    exec_path = os.popen("which adsx").read().strip()

    if not exec_path:
        print("❌ adsx not found in PATH")
        return

    content = SERVICE_TEMPLATE.format(
        user=user,
        home=home,
        exec=exec_path
    )

    print("⚠️ Sudo required to install system service")
    tmp = "/tmp/adsx.service"
    Path(tmp).write_text(content)

    os.system(f"sudo mv {tmp} {SERVICE_PATH}")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo systemctl enable adsx")
    os.system("sudo systemctl start adsx")

    print("✅ AdsX installed & running as background service")
