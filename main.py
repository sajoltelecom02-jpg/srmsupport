import telebot
import json
import os
import threading
import time
from flask import Flask

# --- কনফিগারেশন ---
TOKEN = "8760273912:AAGDpzk_fdOpIe1ltu3EP5cAmJHXW3he3yE"
ADMINS = [5788640897]
MY_CHANNEL_ID = -1002323081321  
MY_GROUP_ID = -1002011910940    
DATA_FILE = "users.json"
BAN_FILE = "banned.json"

bot = telebot.TeleBot(TOKEN)

# --- Flask Server for Render ---
app = Flask('')
@app.route('/')
def home(): return "SRM TELECOM IS LIVE!"

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

def balance_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("Bkash Personal", "Nagad Personal", "Upay Personal")
    markup.add("Bkash Agent", "Nagad Agent", "🏠 মেইন মেনু")
    return markup

def recharge_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("GP Recharge", "BL Recharge", "RB Recharge", "AT Recharge", "🏠 মেইন মেনু")
    return markup

def drive_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("GP Drive", "BL Drive", "RB Drive", "AT Drive", "🏠 মেইন মেনু")
    return markup

def admin_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📊 Total Users", "📜 User Full Details")
    markup.add("🚫 Ban User", "✅ Unban User", "🏠 মেইন মেনু")
    return markup

# --- ফোর্স জয়েন চেক ---
def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return (ch in allowed) and (gr in allowed)
    except: return False

# --- ১. স্টার্ট ও ডাটা কালেকশন ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    banned = load_data(BAN_FILE, [])
    if message.chat.id in banned:
        bot.send_message(uid, "❌ আপনি ব্যানড।")
        return

    users = load_data(DATA_FILE, {})
    if uid not in users:
        users[uid] = {"name": message.from_user.first_name, "phone": "N/A", "loc": "N/A"}
        save_data(DATA_FILE, users)

    if not is_joined(message.chat.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 Channel", url="https://t.me/srmtelecom"),
                   telebot.types.InlineKeyboardButton("👥 Group", url="https://t.me/sajoltelecom2"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I join", callback_data="check_join"))
        bot.send_message(uid, "<b>⚠️ জয়েন বাধ্যতামূলক!</b>\nচ্যানেল ও গ্রুপে জয়েন করে বাটনে ক্লিক করুন।", reply_markup=markup, parse_mode="HTML")
        return

    # নম্বর ও লোকেশন কালেকশন
    if users[uid]["phone"] == "N/A":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📞 নম্বর শেয়ার করুন", request_contact=True))
        bot.send_message(uid, "👋 কাজ শুরু করতে নিচের বাটন চেপে নম্বর দিন।", reply_markup=markup)
    elif users[uid]["loc"] == "N/A":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📍 লোকেশন শেয়ার করুন", request_location=True))
        bot.send_message(uid, "📍 এবার লোকেশনটি শেয়ার করুন।", reply_markup=markup)
    else:
        bot.send_message(uid, f"🌟 <b>S.R.M TELECOM</b>", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

# --- ডাটা রিসিভ (Contact/Location) ---
@bot.message_handler(content_types=['contact', 'location'])
def collect_info(message):
    uid = str(message.chat.id)
    users = load_data(DATA_FILE, {})
    if message.contact: users[uid]["phone"] = message.contact.phone_number
    if message.location: users[uid]["loc"] = f"https://www.google.com/maps?q={message.location.latitude},{message.location.longitude}"
    save_data(DATA_FILE, users)
    start(message)

# --- ২. চ্যানেল পোস্ট অটো ব্রডকাস্ট ---
@bot.channel_post_handler(func=lambda m: m.chat.id == MY_CHANNEL_ID, content_types=['text', 'photo', 'video'])
def auto_broadcast(message):
    users = load_data(DATA_FILE, {})
    for uid in users.keys():
        try:
            if message.content_type == 'text': bot.send_message(uid, message.text, parse_mode="HTML")
            elif message.content_type == 'photo': bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption, parse_mode="HTML")
            elif message.content_type == 'video': bot.send_video(uid, message.video.file_id, caption=message.caption, parse_mode="HTML")
            time.sleep(0.05)
        except: pass

# --- ৩. সাব-বাটন ও সমস্যা কালেকশন (Next Step Handler) ---
def ask_problem(message, sub_name):
    msg = bot.send_message(message.chat.id, f"আপনি <b>{sub_name}</b> বেছে নিয়েছেন।\n\n✅ আপনার সমস্যাটি বিস্তারিত লিখে পাঠান:", parse_mode="HTML", reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, lambda m: ask_screenshot(m, sub_name))

def ask_screenshot(message, sub_name):
    uid = str(message.chat.id)
    # এডমিনকে জানানো
    for admin in ADMINS:
        bot.send_message(admin, f"📩 <b>নতুন রিপোর্ট ({sub_name})</b>\n🆔 ID: <code>{uid}</code>\n📝 সমস্যা: {message.text}", parse_mode="HTML")
    bot.send_message(message.chat.id, "✅ নোট করা হয়েছে। এবার একটি <b>স্ক্রিনশট</b> পাঠান।", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

# --- ৪. মেইন হ্যান্ডলার (বাটন লজিক ও ফরওয়ার্ডিং) ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video'])
def handle_all(message):
    uid = str(message.chat.id)
    text = message.text

    if not is_joined(message.chat.id):
        start(message)
        return

    # বাটন লজিক
    if text == "📲 Apps link": bot.send_message(uid, "🔗 https://play.google.com/store/apps/details?id=com.shuvotelecom24.user")
    elif text == "💰 Balance Problem": bot.send_message(uid, "সিলেক্ট করুন:", reply_markup=balance_menu())
    elif text == "⚡ Recharge Problem": bot.send_message(uid, "অপারেটর:", reply_markup=recharge_menu())
    elif text == "🚗 Drive Problem": bot.send_message(uid, "অপারেটর:", reply_markup=drive_menu())
    elif text == "🏠 মেইন মেনু": start(message)

    # এডমিন প্যানেল বাটন
    elif text == "⚙️ Admin Panel" and message.chat.id in ADMINS:
        bot.send_message(uid, "🛠 এডমিন প্যানেল:", reply_markup=admin_menu())
    elif text == "📊 Total Users" and message.chat.id in ADMINS:
        users = load_data(DATA_FILE, {})
        bot.send_message(uid, f"👥 মোট ইউজার: {len(users)} জন।")
    elif text == "📜 User Full Details" and message.chat.id in ADMINS:
        users = load_data(DATA_FILE, {})
        details = "📜 <b>ইউজার লিস্ট:</b>\n\n"
        for id, info in users.items():
            details += f"👤 {info['name']}\n🆔 <code>{id}</code>\n📞 {info.get('phone','N/A')}\n📍 <a href='{info.get('loc','')}'>Google Map</a>\n---\n"
            if len(details) > 3500:
                bot.send_message(uid, details, parse_mode="HTML", disable_web_page_preview=True)
                details = ""
        bot.send_message(uid, details, parse_mode="HTML", disable_web_page_preview=True)

    # সাব-বাটন ক্লিক চেক
    elif text and ("Recharge" in text or "Drive" in text or "Personal" in text or "Agent" in text):
        ask_problem(message, text)

    # ইউজার কিছু পাঠালে এডমিনকে ফরওয়ার্ড করা
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            bot.forward_message(admin, message.chat.id, message.message_id)
            bot.send_message(admin, f"📩 <b>বার্তা আসিয়াছে</b>\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
        bot.send_message(uid, "✅ আপনার বার্তা এডমিনকে পাঠানো হয়েছে।")

# --- ৫. এডমিন রিপ্লাই লজিক (১০০% ফিক্সড) ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def admin_reply(message):
    try:
        source = message.reply_to_message.text or message.reply_to_message.caption
        if source and "🆔 ID:" in source:
            tid = source.split("🆔 ID:")[1].strip().split("\n")[0].strip()
            if message.content_type == 'text':
                bot.send_message(tid, f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.text}", parse_mode="HTML")
            elif message.content_type == 'photo':
                bot.send_photo(tid, message.photo[-1].file_id, caption=f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.caption if message.caption else ''}", parse_mode="HTML")
            bot.reply_to(message, "✅ রিপ্লাই পাঠানো হয়েছে।")
    except Exception as e: bot.reply_to(message, f"❌ এরর: {str(e)}")

# --- কলব্যাক হ্যান্ডলার (Force Join) ---
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def cb_join(call):
    if is_joined(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    else: bot.answer_callback_query(call.id, "আগে ঠিকভাবে জয়েন করুন! 😡", show_alert=True)

# --- ৬. সার্ভার রান ও পোলিং ---
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))).start()
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except: time.sleep(5)
