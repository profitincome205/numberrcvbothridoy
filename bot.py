import os
import sqlite3
import asyncio
import zipfile
from pyrogram import Client, filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- CONFIGURATION ---
API_ID = 32855082
API_HASH = "5956ab8e405c38833049800ad193efb1"
BOT_TOKEN = "8717585142:AAG8RP5XlXih0iZPEf-ywnqhXMkvRgZqSKE"
ADMIN_ID = 7885781336
WITHDRAW_CH = "hiyghuf" # Channel Link username

app = Client("OfficialOtpBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- DATABASE SETUP ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS countries (flag TEXT, code TEXT, price REAL, name TEXT)")
db.commit()

# Default Settings Setup
def set_default():
    defaults = [("bot_status", "ON"), ("w_status", "ON"), ("min_w", "5.0"), ("max_w", "1000.0"), ("add_time", "10"), ("password", "Hridoy11")]
    for k, v in defaults:
        cursor.execute("INSERT OR IGNORE INTO settings VALUES (?, ?)", (k, v))
    db.commit()
set_default()

def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    return res[0] if res else "0"

# --- KEYBOARDS ---
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Start 🚬"), KeyboardButton("Ballance 💸")],
        [KeyboardButton("Cuntry & Capacity 🛍"), KeyboardButton("Running Prosess Off ❌")],
        [KeyboardButton("Suport & Massage ✉️"), KeyboardButton("Payment & Leader Card Set")]
    ], resize_keyboard=True)

# --- USER HANDLERS ---
@app.on_message(filters.command("start") | filters.regex("Start 🚬"))
async def start_msg(c, m):
    if get_setting("bot_status") == "OFF" and m.from_user.id != ADMIN_ID:
        return await m.reply_text("⛔ Bot is currently OFF by Admin.")
    
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (str(m.from_user.id),))
    db.commit()
    await m.reply_text(f"👋 Welcome {m.from_user.first_name}!\nএটি একটি অরিজিনাল অটোমেটিক নম্বর বট।", reply_markup=main_menu())

@app.on_message(filters.regex("Ballance 💸"))
async def check_bal(c, m):
    cursor.execute("SELECT balance FROM users WHERE id=?", (str(m.from_user.id),))
    bal = cursor.fetchone()[0]
    await m.reply_text(f"💳 **Your Account Balance:** `{bal}$`")

@app.on_message(filters.regex("Cuntry & Capacity 🛍"))
async def cap_list(c, m):
    cursor.execute("SELECT * FROM countries")
    rows = cursor.fetchall()
    if not rows: return await m.reply_text("🛍 বর্তমানে কোনো দেশ বা নম্বর এড করা নেই।")
    
    text = "📊 **Available Capacity & Prices:**\n"
    for r in rows:
        text += f"\n{r[0]} {r[3]} ({r[1]}) — Price: {r[2]}$"
    await m.reply_text(text)

@app.on_message(filters.regex("Payment & Leader Card Set"))
async def withdraw_panel(c, m):
    if get_setting("w_status") == "OFF":
        return await m.reply_text("❌ Withdraw System is currently OFF.")
    
    text = f"🏧 **Withdraw (USDT BEP20)**\n\n💰 Minimum: {get_setting('min_w')}$\n💰 Maximum: {get_setting('max_w')}$\n\nWithdraw দিতে `/withdraw [address] [amount]` এভাবে লিখুন।"
    await m.reply_text(text)

@app.on_message(filters.command("withdraw"))
async def process_w(c, m):
    if len(m.command) < 3: return await m.reply_text("সঠিক নিয়ম: `/withdraw 0xAddress 10`")
    addr, amount = m.command[1], float(m.command[2])
    
    cursor.execute("SELECT balance FROM users WHERE id=?", (str(m.from_user.id),))
    bal = cursor.fetchone()[0]
    
    if amount < float(get_setting("min_w")): return await m.reply_text("❌ মিনিমাম উইথড্র লিমিট কম।")
    if bal < amount: return await m.reply_text("❌ আপনার পর্যাপ্ত ব্যালেন্স নেই।")
    
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, str(m.from_user.id)))
    db.commit()
    
    msg = f"🔔 **Withdraw Request**\nUser: {m.from_user.id}\nAmount: {amount}$\nAddress: `{addr}`"
    await c.send_message(WITHDRAW_CH, msg)
    await m.reply_text("✅ আপনার রিকোয়েস্ট চ্যানেলে পাঠানো হয়েছে।")

# --- ADMIN PANEL ---
@app.on_message(filters.command("Admin") & filters.user(ADMIN_ID))
async def admin_panel(c, m):
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Bot ON", callback_data="b_on"), InlineKeyboardButton("Bot OFF", callback_data="b_off")],
        [InlineKeyboardButton("Withdraw ON", callback_data="w_on"), InlineKeyboardButton("Withdraw OFF", callback_data="w_off")],
        [InlineKeyboardButton("Add Cap (Country)", callback_data="add_c")],
        [InlineKeyboardButton("Session ZIP 📁", callback_data="get_zip")]
    ])
    await m.reply_text("🛠 **অ্যাডমিন প্যানেল**", reply_markup=btn)

@app.on_callback_query()
async def cb_handler(c, q):
    if q.data == "b_on":
        cursor.execute("UPDATE settings SET value='ON' WHERE key='bot_status'")
        await q.answer("Bot is ON", show_alert=True)
    elif q.data == "add_c":
        await q.message.reply_text("দেশ এড করতে এভাবে লিখুন:\n`🇧🇩 +880 0.1 Bangladesh`")

# এডমিন সরাসরি মেসেজ দিলে কান্ট্রি এড হবে
@app.on_message(filters.regex(r"^(.*) (.*) (.*) (.*)$") & filters.user(ADMIN_ID))
async def add_country_logic(c, m):
    p = m.text.split()
    cursor.execute("INSERT INTO countries VALUES (?, ?, ?, ?)", (p[0], p[1], float(p[2]), p[3]))
    db.commit()
    await m.reply_text(f"✅ {p[3]} সফলভাবে এড হয়েছে।")

print("Bot is Live Now!")
app.run()