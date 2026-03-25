import telebot
import json
import os
import threading
from flask import Flask

# --- কনফিগারেশন (আপনার টোকেন ও আইডি) ---
TOKEN = "8760273912:AAEkdvo_gB6yx4Vv--byb0UW_3HKVB9nksE"
ADMINS = [5788640897]
MY_CHANNEL_ID = -1002323081321  
MY_GROUP_ID = -1002011910940    
DATA_FILE = "users.json"
BAN_FILE = "banned.json"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# --- Render Port Fix (Flask) ---
app = Flask('')
@app.route('/')
def home(): return "SRM TELECOM BOT IS ACTIVE!"

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
    markup.add("Bkash Personal", "Nagad Personal", "Upay Personal", "Bkash Agent", "Nagad Agent", "🏠 মেইন মেনু")
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
    markup.add("📊 Total Users", "📜 User Details", "🚫 Ban User", "✅ Unban User", "🏠 মেইন মেনু")
    return markup

# --- Force Join চেক ---
def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return (ch in allowed) and (gr in allowed)
    except: return False

# --- স্টার্ট কমান্ড ও ফোর্স জয়েন ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    banned = load_data(BAN_FILE, [])
    if message.chat.id in banned:
        bot.send_message(uid, "❌ আপনাকে ব্যান করা হয়েছে।")
        return

    # ডাটাবেসে ইউজার সেভ করা
    users = load_data(DATA_FILE, {})
    if uid not in users:
        users[uid] = {"name": message.from_user.first_name, "phone": "Not Shared", "loc": "Not Shared"}
        save_data(DATA_FILE, users)

    if not is_joined(message.chat.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 Channel", url="https://t.me/srmtelecom"),
                   telebot.types.InlineKeyboardButton("👥 Group", url="https://t.me/sajoltelecom2"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I join", callback_data="check_join"))
        bot.send_message(uid, "<b>⚠️ জয়েন বাধ্যতামূলক!</b>\n\nনিচের চ্যানেল ও গ্রুপে জয়েন করে 'I join' বাটনে ক্লিক করুন।", reply_markup=markup, parse_mode="HTML")
        return

    bot.send_message(uid, "🌟 <b>S.R.M TELECOM</b> বটে আপনাকে স্বাগতম!", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_joined(call.message.chat.id):
        bot.answer_callback_query(call.id, "ধন্যবাদ! আপনি সফলভাবে জয়েন করেছেন।")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "আগে ঠিকভাবে জয়েন করুন! 😡", show_alert=True)

# --- সাব-বাটন প্রসেস (সমস্যা -> স্ক্রিনশট) ---
def ask_for_problem(message, sub_name):
    msg = bot.send_message(message.chat.id, f"আপনি <b>{sub_name}</b> সিলেক্ট করেছেন।\n\n✅ আপনার সমস্যাটি বিস্তারিত লিখে পাঠান (নম্বরসহ):", parse_mode="HTML", reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, lambda m: ask_for_screenshot(m, sub_name))

def ask_for_screenshot(message, sub_name):
    uid = str(message.chat.id)
    # এডমিনকে জানানো
    for admin in ADMINS:
        bot.send_message(admin, f"📩 <b>নতুন রিপোর্ট ({sub_name})</b>\n👤 নাম: {message.from_user.first_name}\n📝 বর্ণনা: {message.text}\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
    
    bot.send_message(message.chat.id, "✅ নোট করা হয়েছে। এবার একটি <b>স্ক্রিনশট</b> পাঠান।", reply_markup=main_menu(message.chat.id))

# --- মেইন হ্যান্ডলার ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    text = message.text

    if not is_joined(message.chat.id):
        start(message)
        return

    # মেইন বাটন লজিক
    if text == "📲 Apps link":
        bot.send_message(uid, "<b>📥 অ্যাপ লিঙ্ক:</b>\nhttps://play.google.com/store/apps/details?id=com.shuvotelecom24.user", parse_mode="HTML")
    elif text == "💰 Balance Problem":
        bot.send_message(uid, "মাধ্যম সিলেক্ট করুন:", reply_markup=balance_menu())
    elif text == "⚡ Recharge Problem":
        bot.send_message(uid, "অপারেটর সিলেক্ট করুন:", reply_markup=recharge_menu())
    elif text == "🚗 Drive Problem":
        bot.send_message(uid, "অপারেটর সিলেক্ট করুন:", reply_markup=drive_menu())
    elif text == "🏠 মেইন মেনু": start(message)

    # এডমিন প্যানেল
    elif text == "⚙️ Admin Panel" and message.chat.id in ADMINS:
        bot.send_message(uid, "🛠 এডমিন প্যানেল:", reply_markup=admin_menu())
    elif text == "📊 Total Users" and message.chat.id in ADMINS:
        users = load_data(DATA_FILE, {})
        bot.send_message(uid, f"👥 মোট ইউজার: {len(users)} জন।")
    elif text == "📜 User Details" and message.chat.id in ADMINS:
        users = load_data(DATA_FILE, {})
        details = "📜 <b>ইউজার লিস্ট:</b>\n"
        for id, info in users.items():
            details += f"👤 {info.get('name')} - <code>{id}</code>\n"
        bot.send_message(uid, details, parse_mode="HTML")

    # সাব-বাটন ক্লিক
    elif text and ("Recharge" in text or "Drive" in text or "Personal" in text or "Agent" in text):
        ask_for_problem(message, text)

    # ফরওয়ার্ডিং (ইউজার কিছু পাঠালে)
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            try:
                bot.forward_message(admin, message.chat.id, message.message_id)
                bot.send_message(admin, f"📩 <b>বার্তা আসিয়াছে</b>\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
            except: pass
        bot.send_message(uid, "✅ আপনার বার্তা এডমিনকে পাঠানো হয়েছে।")

# এডমিন রিপ্লাই
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def reply_logic(message):
    try:
        source = message.reply_to_message.text or message.reply_to_message.caption
        if source and "🆔 ID:" in source:
            target_id = source.split("🆔 ID:")[1].strip().split("\n")[0]
            bot.send_message(target_id, f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.text}", parse_mode="HTML")
            bot.reply_to(message, "✅ পাঠানো হয়েছে।")
    except: pass

# --- রান ---
if __name__ == "__main__":
    def run_f(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
    threading.Thread(target=run_f).start()
    bot.infinity_polling()
