import json
import asyncio
import sys
import time
import os
from pathlib import Path
from typing import Dict, Optional
from .systemd import install_service
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= PATHS =================

BASE_DIR = Path.home() / ".adsx"
SESSIONS_DIR = BASE_DIR / "sessions"
CONFIG_FILE = BASE_DIR / "config.json"

BASE_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(exist_ok=True)

# ================= STATE =================

accounts: Dict[str, dict] = {}
active_account: Optional[str] = None
login_tmp: Dict[int, dict] = {}
broadcast_task: Optional[asyncio.Task] = None

# ================= CONFIG =================

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def ensure_config():
    if not CONFIG_FILE.exists():
        save_config({})

def first_run_setup():
    cfg = load_config()
    if cfg.get("api_id") and cfg.get("api_hash") and cfg.get("bot_token"):
        return

    print("\n=== AdsX First Time Setup ===\n")
    cfg = {
        "api_id": int(input("Enter API ID: ").strip()),
        "api_hash": input("Enter API HASH: ").strip(),
        "bot_token": input("Enter BOT TOKEN: ").strip(),
    }
    save_config(cfg)
    print("\n✅ Setup complete. Run `adsx` again.\n")
    sys.exit(0)

# ================= TELETHON =================

async def load_accounts():
    cfg = load_config()
    accounts.clear()

    for f in sorted(SESSIONS_DIR.glob("*.session")):
        acc_id = f.stem
        client = TelegramClient(str(f), cfg["api_id"], cfg["api_hash"])
        await client.connect()

        if not await client.is_user_authorized():
            accounts[acc_id] = {"status": "INACTIVE"}
            continue

        me = await client.get_me()
        groups = []
        async for d in client.iter_dialogs():
            if d.is_group:
                groups.append(d.id)

        accounts[acc_id] = {
            "client": client,
            "phone": me.phone,
            "username": me.username,
            "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
            "groups": groups,
            "status": "ACTIVE",
        }

# ================= WATCHDOG =================

async def watchdog():
    while True:
        await asyncio.sleep(60)

# ================= BOT UI =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🔄 Manage Accounts", callback_data="manage")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🛑 Stop", callback_data="stop")],
    ]
    await update.message.reply_text(
        "AdsX Control Panel",
        reply_markup=InlineKeyboardMarkup(kb),
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_account, broadcast_task
    q = update.callback_query
    await q.answer()

    if q.data == "manage":
        kb = [
            [InlineKeyboardButton("📱 Login with Number", callback_data="login_phone")],
            [InlineKeyboardButton("📁 Upload Session File", callback_data="upload")],
            [InlineKeyboardButton("🔁 Change Active Account", callback_data="change")],
            [InlineKeyboardButton("📊 Account Status", callback_data="status")],
        ]
        await q.edit_message_text("Manage Accounts", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "login_phone":
        context.user_data.clear()
        context.user_data["mode"] = "phone"
        await q.edit_message_text("Send phone number with country code")

    elif q.data == "upload":
        context.user_data.clear()
        context.user_data["mode"] = "upload"
        await q.edit_message_text("Send .session file")

    elif q.data == "change":
        kb = []
        for acc, info in accounts.items():
            if info.get("status") != "ACTIVE":
                continue
            label = " | ".join(
                p for p in [
                    f"@{info['username']}" if info.get("username") else None,
                    info.get("phone"),
                    info.get("name"),
                ] if p
            )
            kb.append([InlineKeyboardButton(label, callback_data=f"use:{acc}")])
        await q.edit_message_text("Select Active Account", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("use:"):
        active_account = q.data.split(":", 1)[1]
        if broadcast_task:
            broadcast_task.cancel()
            broadcast_task = None
        await q.edit_message_text("✅ Active account changed\n🛑 Broadcast stopped")

    elif q.data == "status":
        text = "📊 Account Status\n\n"
        for acc, info in accounts.items():
            if info.get("status") == "ACTIVE":
                text += f"{acc}\n@{info['username']} | {info['phone']} | {info['name']}\n🟢 ACTIVE | Groups: {len(info['groups'])}\n\n"
            else:
                text += f"{acc}\n🔴 INACTIVE\n\n"
        await q.edit_message_text(text)

    elif q.data == "stop":
        await stop_broadcast(update, context)

# ================= LOGIN =================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    chat_id = update.effective_chat.id

    if context.user_data.get("mode") == "phone":
        phone = update.message.text.strip()
        acc_id = f"acc{len(accounts) + 1}"
        client = TelegramClient(str(SESSIONS_DIR / acc_id), cfg["api_id"], cfg["api_hash"])
        await client.connect()
        await client.send_code_request(phone)
        login_tmp[chat_id] = {"client": client, "phone": phone, "acc_id": acc_id}
        context.user_data["mode"] = "otp"
        await update.message.reply_text("Send OTP")
        return

    if context.user_data.get("mode") == "otp":
        data = login_tmp[chat_id]
        try:
            await data["client"].sign_in(data["phone"], update.message.text.strip())
        except SessionPasswordNeededError:
            context.user_data["mode"] = "password"
            await update.message.reply_text("Send 2FA password")
            return
        await finalize_login(update, context, data)
        return

    if context.user_data.get("mode") == "password":
        data = login_tmp[chat_id]
        await data["client"].sign_in(password=update.message.text.strip())
        await finalize_login(update, context, data)
        return

    if context.user_data.get("mode") == "broadcast":
        await start_broadcast(update, context)

async def finalize_login(update, context, data):
    me = await data["client"].get_me()
    groups = []
    async for d in data["client"].iter_dialogs():
        if d.is_group:
            groups.append(d.id)

    accounts[data["acc_id"]] = {
        "client": data["client"],
        "phone": me.phone,
        "username": me.username,
        "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
        "groups": groups,
        "status": "ACTIVE",
    }

    global active_account
    active_account = data["acc_id"]
    context.user_data.clear()
    login_tmp.pop(update.effective_chat.id, None)

    await update.message.reply_text(f"✅ Account Added\n@{me.username}\nGroups: {len(groups)}")

# ================= SESSION UPLOAD =================

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") != "upload":
        return

    cfg = load_config()
    acc_id = f"acc{len(accounts) + 1}"
    path = SESSIONS_DIR / acc_id

    file = await update.message.document.get_file()
    await file.download_to_drive(str(path) + ".session")

    client = TelegramClient(str(path), cfg["api_id"], cfg["api_hash"])
    await client.connect()

    if not await client.is_user_authorized():
        await update.message.reply_text("❌ Invalid session")
        context.user_data.clear()
        return

    me = await client.get_me()
    groups = []
    async for d in client.iter_dialogs():
        if d.is_group:
            groups.append(d.id)

    accounts[acc_id] = {
        "client": client,
        "phone": me.phone,
        "username": me.username,
        "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
        "groups": groups,
        "status": "ACTIVE",
    }

    global active_account
    active_account = acc_id
    context.user_data.clear()

    await update.message.reply_text(f"✅ Session Added\n@{me.username}\nGroups: {len(groups)}")

# ================= BROADCAST =================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_account:
        await update.message.reply_text("❌ No active account selected")
        return

    delay = 0
    if context.args and context.args[0].endswith("m"):
        delay = int(context.args[0][:-1]) * 60

    context.user_data.clear()
    context.user_data["mode"] = "broadcast"
    context.user_data["delay"] = delay

    await update.message.reply_text("Send message link")

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_task

    link = update.message.text.strip()
    msg_id = int(link.split("/")[-1])
    src = link.split("/")[-2]

    acc = accounts[active_account]
    delay = context.user_data.get("delay", 0)

    status_msg = await update.message.reply_text("🚀 Broadcast started")

    if broadcast_task:
        broadcast_task.cancel()

    broadcast_task = asyncio.create_task(
        broadcast_loop(
            context.application,
            update.effective_chat.id,
            status_msg.message_id,
            acc["client"],
            acc["groups"],
            src,
            msg_id,
            delay,
        )
    )

    context.user_data.clear()

async def broadcast_loop(app, chat_id, msg_id, client, groups, src, mid, delay):
    while True:
        for gid in groups:
            try:
                msg = await client.get_messages(src, ids=mid)
                await client.forward_messages(gid, msg)
                await asyncio.sleep(3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                pass

        if delay == 0:
            break
        await asyncio.sleep(delay)

async def stop_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_task
    if broadcast_task:
        broadcast_task.cancel()
        broadcast_task = None
        text = "🛑 Broadcast stopped"
    else:
        text = "No broadcast running"

    if update.callback_query:
        await update.callback_query.message.edit_text(text)
    else:
        await update.message.reply_text(text)

# ================= MAIN =================

def main():
    first_run_setup()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(load_accounts())
    loop.create_task(watchdog())

    cfg = load_config()
    app = ApplicationBuilder().token(cfg["bot_token"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stop", stop_broadcast))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))

    print("AdsX Bot Running...")
    app.run_polling()

# ================= CLI =================

def daemon():
    """
    systemd entrypoint – NO input(), NO CLI, NO exit
    """
    cfg = load_config()
    if not cfg.get("bot_token"):
        print("❌ Bot token missing. Run adsx locally first.")
        while True:
            time.sleep(60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(load_accounts())
    loop.create_task(watchdog())

    app = ApplicationBuilder().token(cfg["bot_token"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stop", stop_broadcast))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))

    print("AdsX daemon running")
    app.run_polling(close_loop=False)

def is_service_installed():
    return os.path.exists("/etc/systemd/system/adsx.service")
def has_systemd():
    return os.path.exists("/bin/systemctl") or os.path.exists("/usr/bin/systemctl")

def run():
    # ---------- CLI ARGUMENT MODE ----------
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "install":
            install_service()
            print("✅ AdsX installed. From now on just run: adsx")
            return

        if cmd == "bottoken":
            ensure_config()
            cfg = load_config()
            cfg["bot_token"] = input("Enter new BOT TOKEN: ").strip()
            save_config(cfg)
            print("✅ Bot token updated")
            return

        if cmd == "api":
            ensure_config()
            cfg = load_config()
            cfg["api_id"] = int(input("Enter API ID: ").strip())
            cfg["api_hash"] = input("Enter API HASH: ").strip()
            save_config(cfg)
            print("✅ API updated")
            return

        if cmd == "reset":
            reset_all()
            print("✅ AdsX reset")
            return

        if cmd == "fg":
            main()
            return

    # ---------- NO ARGUMENTS ----------
    if has_systemd() and is_service_installed():
        os.system("systemctl start adsx")
        print("🚀 AdsX running in background")
        return

    if not has_systemd():
        print("⚠️ systemd not available (macOS detected)")
        print("👉 Run with: adsx fg")
        return

    print("❌ AdsX is not installed yet")
    print("👉 Run: adsx install")
