import telebot
import json
import os
import threading
from flask import Flask

# --- কনফিগারেশন ---
TOKEN = "8760273912:AAEkdvo_gB6yx4Vv--byb0UW_3HKVB9nksE"
ADMINS = [5788640897]
MY_CHANNEL_ID = -1002323081321  
MY_GROUP_ID = -1002011910940    
DATA_FILE = "users.json"
BAN_FILE = "banned.json"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# --- Render Port Fix ---
app = Flask('')
@app.route('/')
def home(): return "SRM TELECOM BOT IS LIVE!"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# --- ডাটাবেস হ্যান্ডলিং ---
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

# --- কিবোর্ড মেনুসমূহ ---
def main_menu(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📲 Apps link", "💰 Balance Problem")
    markup.add("⚡ Recharge Problem", "🚗 Drive Problem")
    markup.add("☎️ সহযোগিতা (Support)")
    if user_id in ADMINS: markup.add("⚙️ Admin Panel")
    return markup

def admin_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📊 Total Users", "📜 User Details")
    markup.add("🚫 Ban User", "✅ Unban User")
    markup.add("🏠 মেইন মেনু")
    return markup

# --- চেক ফাংশন ---
def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        return ch in ['member', 'administrator', 'creator'] and gr in ['member', 'administrator', 'creator']
    except: return False

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    banned = load_data(BAN_FILE, [])
    if message.chat.id in banned:
        bot.send_message(uid, "❌ আপনাকে ব্যান করা হয়েছে।")
        return

    users = load_data(DATA_FILE, {})
    if uid not in users:
        users[uid] = {"name": message.from_user.first_name, "phone": "Not Shared", "loc": "Not Shared"}
        save_data(DATA_FILE, users)

    if not is_joined(message.chat.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 Channel", url="https://t.me/srmtelecom"),
                   telebot.types.InlineKeyboardButton("👥 Group", url="https://t.me/sajoltelecom2"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I join", callback_data="check_join"))
        bot.send_message(uid, "<b>⚠️ জয়েন বাধ্যতামূলক!</b>", reply_markup=markup, parse_mode="HTML")
        return

    # ফোন নম্বর এবং লোকেশন না থাকলে চেয়ে নেওয়া
    if users[uid]["phone"] == "Not Shared":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📞 নম্বর শেয়ার করুন", request_contact=True))
        bot.send_message(uid, "👋 কাজ শুরু করতে আপনার নম্বরটি শেয়ার করুন।", reply_markup=markup)
    elif users[uid]["loc"] == "Not Shared":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📍 লোকেশন শেয়ার করুন", request_location=True))
        bot.send_message(uid, "📍 এবার আপনার লোকেশনটি শেয়ার করুন।", reply_markup=markup)
    else:
        bot.send_message(uid, f"🌟 <b>S.R.M TELECOM</b>\nস্বাগতম {users[uid]['name']}!", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

# ডাটা সংগ্রহ (Contact & Location)
@bot.message_handler(content_types=['contact', 'location'])
def collect_info(message):
    uid = str(message.chat.id)
    users = load_data(DATA_FILE, {})
    if message.contact:
        users[uid]["phone"] = message.contact.phone_number
    if message.location:
        users[uid]["loc"] = f"https://www.google.com/maps?q={message.location.latitude},{message.location.longitude}"
    save_data(DATA_FILE, users)
    start(message)

# --- এডমিন অ্যাকশন ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "📜 User Details")
def show_details(message):
    users = load_data(DATA_FILE, {})
    if not users:
        bot.send_message(message.chat.id, "এখনো কোনো ইউজার নেই।")
        return
    
    details_txt = "📜 <b>ইউজারদের পূর্ণাঙ্গ তথ্য:</b>\n\n"
    for id, info in users.items():
        details_txt += f"👤 <b>নাম:</b> {info.get('name')}\n"
        details_txt += f"🆔 <b>ID:</b> <code>{id}</code>\n"
        details_txt += f"📞 <b>ফোন:</b> {info.get('phone')}\n"
        details_txt += f"📍 <b>লোকেশন:</b> <a href='{info.get('loc')}'>ম্যাপে দেখুন</a>\n"
        details_txt += "------------------------\n"
        
        # মেসেজ অনেক বড় হয়ে গেলে ভেঙে পাঠানো
        if len(details_txt) > 3000:
            bot.send_message(message.chat.id, details_txt, parse_mode="HTML", disable_web_page_preview=True)
            details_txt = ""
            
    bot.send_message(message.chat.id, details_txt, parse_mode="HTML", disable_web_page_preview=True)

# --- (বাকি বাটন লজিক এবং রিপ্লাই লজিক আগের মতোই থাকবে) ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    # ... (এখানে রিচার্জ, ড্রাইভ এবং ব্যালেন্সের বাটন লজিকগুলো থাকবে যা আগে দিয়েছি) ...
    # সজল ভাই, নিচের এই অংশটি শুধু এডমিন প্যানেল দেখানোর জন্য:
    if message.text == "⚙️ Admin Panel" and message.chat.id in ADMINS:
        bot.send_message(uid, "🛠 এডমিন প্যানেল:", reply_markup=admin_menu())
    elif message.text == "📊 Total Users" and message.chat.id in ADMINS:
        users = load_data(DATA_FILE, {})
        bot.send_message(uid, f"👥 মোট ইউজার: {len(users)} জন।")
    elif message.text == "🏠 মেইন মেনু":
        start(message)
    # ফরওয়ার্ডিং এবং অন্যান্য লজিক...
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            bot.forward_message(admin, message.chat.id, message.message_id)
            bot.send_message(admin, f"📩 <b>বার্তা আসিয়াছে</b>\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
        bot.send_message(uid, "✅ এডমিনকে জানানো হয়েছে।")

# রিপ্লাই লজিক আগের মতোই...
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def reply_logic(message):
    try:
        source_text = message.reply_to_message.text or message.reply_to_message.caption
        if source_text and "🆔 ID:" in source_text:
            target_id = source_text.split("🆔 ID:")[1].strip().split("\n")[0]
            bot.send_message(target_id, f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.text}", parse_mode="HTML")
            bot.reply_to(message, "✅ পাঠানো হয়েছে।")
    except: pass

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.infinity_polling()
