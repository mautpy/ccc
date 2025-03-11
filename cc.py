import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Configuration
API_ID = "22625636"
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"
BOT_TOKEN = "7711228084:AAF5KucOQFvpsvD29cVZRU8K3RqXnCKD3rk"
CHANNEL_USERNAME = "seedhe_maut"  # Use username instead of channel ID
CHANNEL_LINK = "https://t.me/seedhe_maut"  # Your channel join link

# Initialize bot
bot = Client("host_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to check if user joined the channel
async def is_member(client, user_id):
    try:
        member = await client.get_chat_member(CHANNEL_USERNAME, user_id)  # Use username
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking membership: {e}")  # Debugging
        return False

# Start Command
@bot.on_message(filters.command("start"))
async def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🔄 Check", callback_data="check_join")]
    ])
    await message.reply("👋 Welcome! Please join the channel to use this bot.", reply_markup=keyboard)

# Button Handler for Check
@bot.on_callback_query(filters.regex("check_join"))
async def check_join(client, callback_query):
    user_id = callback_query.from_user.id
    if await is_member(client, user_id):
        await callback_query.message.edit_text("✅ You have joined the channel! Now you can use the bot.")
    else:
        await callback_query.answer("❌ You haven't joined yet!", show_alert=True)

# Middleware to check user is in the channel
@bot.on_message(filters.command(["host"]))
async def check_channel(client, message):
    user_id = message.from_user.id
    if not await is_member(client, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Check", callback_data="check_join")]
        ])
        await message.reply("❌ You must join the channel to use this command.", reply_markup=keyboard)
        return
    await message.reply("📂 Send any Python (.py) file to host.")

# Hosting Python files
@bot.on_message(filters.document)
async def host_python_file(client, message):
    if not message.document.file_name.endswith(".py"):
        await message.reply("❌ Please send a valid Python (.py) file.")
        return

    file_path = await message.download()
    await message.reply(f"🚀 Hosting `{message.document.file_name}`...")

    # Run the script in the background
    process = subprocess.Popen(["python3", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    await message.reply(f"✅ `{message.document.file_name}` is now running!\nProcess ID: `{process.pid}`")

# Run the bot
bot.run()
