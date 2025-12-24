import os
import getpass
from pathlib import Path

SERVICE_PATH = "/etc/systemd/system/adsc.service"

SERVICE_TEMPLATE = """[Unit]
Description=AdsC Telegram Bot
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
    exec_path = os.popen("which adsc").read().strip()

    if not exec_path:
        print("❌ adsc not found in PATH")
        return

    content = SERVICE_TEMPLATE.format(
        user=user,
        home=home,
        exec=exec_path
    )

    tmp = "/tmp/adsc.service"
    Path(tmp).write_text(content)

    os.system(f"sudo mv {tmp} {SERVICE_PATH}")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo systemctl enable adsc")
    os.system("sudo systemctl restart adsc")

    print("✅ AdsC installed & running as background service")
