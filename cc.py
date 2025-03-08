import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = 22625636  # Replace with your API ID
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"  # Replace with your API Hash
BOT_TOKEN = "7821220674:AAE9tWHbpxxbEOajtnPWXv7WsAbS3UG4Ly0"  # Replace with your bot token
CHANNEL_ID = -1002363906868  # Replace with your channel ID
ADMINS = [7017469802]  # Replace with your admin user IDs

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

hosted_scripts = {}  # {user_id: [{"file": path, "process": process}]}
approved_users = set()  # Users approved for unlimited script hosting

# Check if user joined the required channel
async def is_user_joined(client, user_id):
    try:
        user = await client.get_chat_member(CHANNEL_ID, user_id)
        return user.status in ["member", "administrator", "creator"]
    except:
        return False

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/seedhe_maut")],
        [InlineKeyboardButton("✅ Check", callback_data="check")]
    ])
    await message.reply_text(
        "🔥 **Welcome to the Hosting Bot!**\n\n"
        "Join our channel to use the bot and host Python scripts.\n"
        "Click **Check** after joining.",
        reply_markup=buttons
    )

# Callback for checking channel join
@app.on_callback_query(filters.regex("check"))
async def check_channel(client, callback_query):
    if await is_user_joined(client, callback_query.from_user.id):
        await callback_query.answer("✅ You have joined! You can now use the bot.", show_alert=True)
    else:
        await callback_query.answer("❌ You haven't joined the channel yet!", show_alert=True)

# Host Python script
@app.on_message(filters.command("host"))
async def host_script(client, message):
    user_id = message.from_user.id

    if not await is_user_joined(client, user_id):
        await message.reply_text("❌ **You must join the channel first!**")
        return

    if message.reply_to_message and message.reply_to_message.document:
        file = message.reply_to_message.document
        if not file.file_name.endswith(".py"):
            await message.reply_text("❌ **Only .py files are allowed!**")
            return

        if user_id not in hosted_scripts:
            hosted_scripts[user_id] = []

        # Restrict normal users to 2 scripts
        if user_id not in approved_users and user_id not in ADMINS and len(hosted_scripts[user_id]) >= 2:
            await message.reply_text("❌ **You can only host 2 scripts!** Request admin approval for unlimited hosting.")
            return

        file_path = await message.reply_to_message.download()
        process = await asyncio.create_subprocess_exec("python3", file_path)

        hosted_scripts[user_id].append({"file": file_path, "process": process})
        await message.reply_text(f"✅ **Hosting `{file.file_name}` successfully!**")

# Stop hosted script
@app.on_message(filters.command("stop"))
async def stop_script(client, message):
    user_id = message.from_user.id
    user_scripts = hosted_scripts.get(user_id, [])

    if user_scripts:
        script_info = user_scripts.pop()
        script_info["process"].terminate()
        os.remove(script_info["file"])
        await message.reply_text("✅ **Your script has been stopped.**")
    else:
        await message.reply_text("❌ **You have no active scripts.**")

# Restart hosted script
@app.on_message(filters.command("restart"))
async def restart_script(client, message):
    user_id = message.from_user.id
    user_scripts = hosted_scripts.get(user_id, [])

    if user_scripts:
        script_info = user_scripts[0]
        script_info["process"].terminate()
        await asyncio.sleep(1)  # Ensure process is stopped
        process = await asyncio.create_subprocess_exec("python3", script_info["file"])
        script_info["process"] = process
        await message.reply_text("✅ **Script restarted successfully.**")
    else:
        await message.reply_text("❌ **No active script found to restart.**")

# Approve user for unlimited hosting (Admins only)
@app.on_message(filters.command("approve") & filters.user(ADMINS))
async def approve_user(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Usage:** `/approve <user_id>`")
        return

    try:
        user_id = int(message.command[1])
        approved_users.add(user_id)
        await message.reply_text(f"✅ **User `{user_id}` approved for unlimited hosting!**")
    except ValueError:
        await message.reply_text("❌ **Invalid user ID.**")

# List active scripts
@app.on_message(filters.command("list"))
async def list_scripts(client, message):
    user_id = message.from_user.id

    if user_id in ADMINS:
        # Admins see all scripts
        all_scripts = "\n".join([f"👤 `{uid}`: {len(scripts)} scripts" for uid, scripts in hosted_scripts.items()])
        await message.reply_text(f"📜 **All Running Scripts:**\n\n{all_scripts or 'No active scripts.'}")
    else:
        # Users see only their scripts
        user_scripts = hosted_scripts.get(user_id, [])
        await message.reply_text(f"📜 **Your Running Scripts:** {len(user_scripts)}")

app.run()
