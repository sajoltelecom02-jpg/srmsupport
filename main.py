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

# --- ডাটাবেস ফাংশন ---
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

# --- কিবোর্ড মেনু ---
def main_menu(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📲 Apps link", "💰 Balance Problem")
    markup.add("⚡ Recharge Problem", "🚗 Drive Problem")
    markup.add("☎️ সহযোগিতা (Support)")
    if user_id in ADMINS: markup.add("⚙️ Admin Panel")
    return markup

def admin_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📊 Total Users", "📜 User Full Details")
    markup.add("🚫 Ban User", "✅ Unban User")
    markup.add("🏠 মেইন মেনু")
    return markup

# --- জয়েন চেক ---
def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return (ch in allowed) and (gr in allowed)
    except: return False

# --- স্টার্ট কমান্ড ---
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

    bot.send_message(uid, "🌟 <b>S.R.M TELECOM</b>", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_joined(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    else: bot.answer_callback_query(call.id, "আগে জয়েন করুন! 😡", show_alert=True)

# --- ডাটা সংগ্রহ (Contact & Location) ---
@bot.message_handler(content_types=['contact', 'location'])
def collect_info(message):
    uid = str(message.chat.id)
    users = load_data(DATA_FILE, {})
    if uid not in users: users[uid] = {}
    
    if message.contact:
        users[uid]["phone"] = message.contact.phone_number
        bot.send_message(uid, "✅ ফোন নম্বর সেভ হয়েছে। এবার লোকেশন শেয়ার করুন।")
    if message.location:
        users[uid]["loc"] = f"https://www.google.com/maps?q={message.location.latitude},{message.location.longitude}"
        bot.send_message(uid, "✅ লোকেশন সেভ হয়েছে।")
    
    save_data(DATA_FILE, users)
    start(message)

# --- এডমিন প্যানেল লজিক ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "📜 User Full Details")
def show_full_details(message):
    users = load_data(DATA_FILE, {})
    if not users:
        bot.send_message(message.chat.id, "এখনো কোনো ইউজার ডাটা নেই।")
        return
    
    msg_list = []
    current_msg = "📜 <b>ইউজারদের পূর্ণাঙ্গ তথ্য:</b>\n\n"
    
    for uid, info in users.items():
        user_info = f"👤 <b>নাম:</b> {info.get('name', 'N/A')}\n"
        user_info += f"🆔 <b>ID:</b> <code>{uid}</code>\n"
        user_info += f"📞 <b>ফোন:</b> {info.get('phone', 'Not Shared')}\n"
        loc = info.get('loc', 'Not Shared')
        if "http" in loc:
            user_info += f"📍 <b>লোকেশন:</b> <a href='{loc}'>ম্যাপ লিঙ্ক</a>\n"
        else:
            user_info += f"📍 <b>লোকেশন:</b> {loc}\n"
        user_info += "------------------------\n"
        
        # টেলিগ্রামের মেসেজ লিমিট (৪০৯৬ ক্যারেক্টার) হ্যান্ডেল করা
        if len(current_msg + user_info) > 3500:
            msg_list.append(current_msg)
            current_msg = user_info
        else:
            current_msg += user_info
    
    msg_list.append(current_msg)
    
    for m in msg_list:
        bot.send_message(message.chat.id, m, parse_mode="HTML", disable_web_page_preview=True)

# --- রিপ্লাই ও ফরওয়ার্ডিং ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    text = message.text

    # এডমিন বাটন
    if text == "⚙️ Admin Panel" and message.chat.id in ADMINS:
        bot.send_message(uid, "🛠 এডমিন প্যানেল:", reply_markup=admin_menu())
    elif text == "📊 Total Users" and message.chat.id in ADMINS:
        users = load_data(DATA_FILE, {})
        bot.send_message(uid, f"👥 মোট ইউজার: {len(users)} জন।")
    elif text == "🏠 মেইন মেনু": start(message)

    # সাব-বাটন হ্যান্ডলিং (আগে যা ছিল তাই থাকবে)
    elif text and ("Recharge" in text or "Drive" in text or "Personal" in text or "Agent" in text):
        msg = bot.send_message(uid, f"আপনি <b>{text}</b> সিলেক্ট করেছেন। সমস্যাটি লিখে পাঠান:", parse_mode="HTML", reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: bot.send_message(uid, "📝 নোট করা হয়েছে। এবার একটি স্ক্রিনশট দিন।", reply_markup=main_menu(uid)))

    # ফরওয়ার্ডিং
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            bot.forward_message(admin, message.chat.id, message.message_id)
            bot.send_message(admin, f"📩 <b>বার্তা আসিয়াছে</b>\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
        bot.send_message(uid, "✅ এডমিনকে জানানো হয়েছে।")

# রিপ্লাই লজিক
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def reply_logic(message):
    try:
        source = message.reply_to_message.text or message.reply_to_message.caption
        if source and "🆔 ID:" in source:
            target_id = source.split("🆔 ID:")[1].strip().split("\n")[0]
            bot.send_message(target_id, f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.text}", parse_mode="HTML")
            bot.reply_to(message, "✅ পাঠানো হয়েছে।")
    except: pass

if __name__ == "__main__":
    def run_f():
        try: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
        except: pass
    threading.Thread(target=run_f).start()
    bot.infinity_polling(skip_pending=True)
