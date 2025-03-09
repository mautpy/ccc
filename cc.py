import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

API_ID = 22625636  
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"  
BOT_TOKEN = "7821220674:AAE9tWHbpxxbEOajtnPWXv7WsAbS3UG4Ly0"  
CHANNEL_ID = -1002363906868  
FORWARD_CHANNEL = -1002263829808  
ADMINS = [7017469802]  

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

hosted_scripts = {}  
approved_users = set()  
waiting_for_file = {}  

# Check if user joined the required channel
async def is_user_joined(client, user_id):
    try:
        user = await client.get_chat_member(CHANNEL_ID, user_id)
        return user.status not in ["left", "kicked"]
    except:
        return False

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    save_user(user_id)  

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/seedhe_maut")],
        [InlineKeyboardButton("✅ Check", callback_data="check")]
    ])

    image_url = "https://t.me/seedhe_maut_owner9/34"  

    await client.send_photo(
        chat_id=message.chat.id,
        photo=image_url,
        caption="🔥 **Welcome to the Hosting Bot!**\n\n"
                "Join our channel to use the bot and host Python scripts.\n"
                "Click **Check** after joining.",
        reply_markup=buttons
    )

# Save user ID
def save_user(user_id):
    with open("users.txt", "a+") as f:
        f.seek(0)
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

# Check channel join
@app.on_callback_query(filters.regex("check"))
async def check_channel(client, callback_query):
    user_id = callback_query.from_user.id
    if await is_user_joined(client, user_id):
        await callback_query.answer("✅ You have joined! You can now use the bot.", show_alert=True)
    else:
        await callback_query.answer("❌ You haven't joined the channel yet!", show_alert=True)

# Step 1: Ask user to send a .py file
@app.on_message(filters.command("host"))
async def ask_for_file(client, message):
    user_id = message.from_user.id

    if not await is_user_joined(client, user_id):
        await message.reply_text("❌ **You must join the channel first!**")
        return

    waiting_for_file[user_id] = True  
    await message.reply_text("📂 **Send the .py file you want to host.**", reply_markup=ForceReply(selective=True))

# Step 2: Handle file upload & hosting
@app.on_message(filters.document & filters.private)
async def host_script(client, message):
    user_id = message.from_user.id

    # Debugging: Check if user is in waiting list
    if user_id not in waiting_for_file:
        await message.reply_text("❌ **Please use /host first before sending a file.**")
        return  

    del waiting_for_file[user_id]  

    if not await is_user_joined(client, user_id):
        await message.reply_text("❌ **You must join the channel first!**")
        return

    file = message.document
    if not file.file_name.endswith(".py"):
        await message.reply_text("❌ **Only .py files are allowed!**")
        return

    if user_id not in hosted_scripts:
        hosted_scripts[user_id] = []

    # Restrict normal users to 2 scripts
    if user_id not in approved_users and user_id not in ADMINS and len(hosted_scripts[user_id]) >= 2:
        await message.reply_text("❌ **You can only host 2 scripts!** Request admin approval for unlimited hosting.")
        return

    file_path = await message.download()
    process = await asyncio.create_subprocess_exec("python3", file_path)

    hosted_scripts[user_id].append({"file": file_path, "process": process})

    # Forward the file to the storage channel
    await client.send_document(FORWARD_CHANNEL, file_path, caption=f"📂 Hosted by `{message.from_user.id}`")

    await message.reply_text(f"✅ **Hosting `{file.file_name}` successfully!**")

# Stop hosted script (Users stop their own, Admins stop any)
@app.on_message(filters.command("stop"))
async def stop_script(client, message):
    user_id = message.from_user.id
    command_parts = message.text.split()

    if user_id in ADMINS and len(command_parts) > 1:
        try:
            target_user = int(command_parts[1])
            if target_user in hosted_scripts and hosted_scripts[target_user]:
                script_info = hosted_scripts[target_user].pop()
                script_info["process"].terminate()
                os.remove(script_info["file"])
                await message.reply_text(f"✅ **Stopped a script for user `{target_user}`.**")
            else:
                await message.reply_text("❌ **No active scripts found for this user.**")
        except ValueError:
            await message.reply_text("❌ **Invalid user ID.**")
        return

    # Normal user stopping their own script
    user_scripts = hosted_scripts.get(user_id, [])
    if not user_scripts:
        await message.reply_text("❌ **You have no active scripts.**")
        return

    script_info = user_scripts.pop()
    script_info["process"].terminate()
    os.remove(script_info["file"])
    await message.reply_text("✅ **Your script has been stopped.**")

# Restart hosted script
@app.on_message(filters.command("restart"))
async def restart_script(client, message):
    user_id = message.from_user.id
    user_scripts = hosted_scripts.get(user_id, [])

    if not user_scripts:
        await message.reply_text("❌ **No active script found to restart.**")
        return

    script_info = user_scripts[0]
    script_info["process"].terminate()
    await asyncio.sleep(1)  
    process = await asyncio.create_subprocess_exec("python3", script_info["file"])
    script_info["process"] = process
    await message.reply_text("✅ **Script restarted successfully.**")

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
        all_scripts = "\n".join([f"👤 `{uid}`: {len(scripts)} scripts" for uid, scripts in hosted_scripts.items()])
        await message.reply_text(f"📜 **All Running Scripts:**\n\n{all_scripts or 'No active scripts.'}")
    else:
        user_scripts = hosted_scripts.get(user_id, [])
        await message.reply_text(f"📜 **Your Running Scripts:** {len(user_scripts)}")

app.run()
