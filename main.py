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

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# --- Render এরর ফিক্স (Flask Server) ---
app = Flask('')

@app.route('/')
def home():
    return "SRM TELECOM BOT IS ALIVE!"

def run_web():
    # Render সাধারণত পোর্ট ১০০০০ ব্যবহার করে
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# --- ডাটাবেস হ্যান্ডলিং ---
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- কিবোর্ড মেনুসমূহ ---
def main_menu(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📲 Apps link", "💰 Balance Problem")
    markup.add("⚡ Recharge Problem", "🚗 Drive Problem")
    markup.add("☎️ সহযোগিতা (Support)")
    if user_id in ADMINS:
        markup.add("⚙️ Admin Panel")
    return markup

def balance_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("Bkash Personal", "Nagad Personal", "Upay Personal")
    markup.add("Bkash Agent", "Nagad Agent")
    markup.add("🏠 মেইন মেনু")
    return markup

def recharge_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("GP Recharge", "BL Recharge", "RB Recharge", "AT Recharge")
    markup.add("🏠 মেইন মেনু")
    return markup

def drive_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("GP Drive", "BL Drive", "RB Drive", "AT Drive")
    markup.add("🏠 মেইন মেনু")
    return markup

def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return ch in allowed and gr in allowed
    except: return False

# --- হ্যান্ডলারসমূহ ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    users = load_data(DATA_FILE, {})
    if uid not in users:
        users[uid] = {"phone": None, "loc": None}
        save_data(DATA_FILE, users)

    if not is_joined(message.chat.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 Channel", url="https://t.me/srmtelecom"),
                   telebot.types.InlineKeyboardButton("👥 Group", url="https://t.me/sajoltelecom2"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I join", callback_data="check_join"))
        bot.send_message(uid, "<b>⚠️ জয়েন বাধ্যতামূলক!</b>", reply_markup=markup, parse_mode="HTML")
        return

    if not users[uid].get("phone"):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📞 নম্বর শেয়ার", request_contact=True))
        bot.send_message(uid, "👋 কাজ শুরু করতে নম্বর শেয়ার করুন।", reply_markup=markup)
    elif not users[uid].get("loc"):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📍 লোকেশন শেয়ার", request_location=True))
        bot.send_message(uid, "📍 এবার লোকেশন শেয়ার করুন।", reply_markup=markup)
    else:
        bot.send_message(uid, "🌟 <b>S.R.M TELECOM</b>", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_joined(call.message.chat.id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "আগে ঠিকভাবে জয়েন করুন! 😡", show_alert=True)

@bot.message_handler(content_types=['contact', 'location'])
def data_collect(message):
    uid = str(message.chat.id)
    users = load_data(DATA_FILE, {})
    if message.contact: users[uid]["phone"] = message.contact.phone_number
    if message.location: users[uid]["loc"] = f"{message.location.latitude},{message.location.longitude}"
    save_data(DATA_FILE, users)
    start(message)

# --- গ্লোবাল মেসেজ হ্যান্ডলার ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    text = message.text

    if text == "📲 Apps link":
        bot.send_message(uid, "<b>📥 অ্যাপ লিঙ্ক:</b>\nhttps://play.google.com/store/apps/details?id=com.shuvotelecom24.user", parse_mode="HTML")
    elif text == "💰 Balance Problem":
        bot.send_message(uid, "কোন মাধ্যমে টাকা পাঠিয়েছেন?", reply_markup=balance_menu())
    elif text == "⚡ Recharge Problem":
        bot.send_message(uid, "কোন অপারেটরে রিচার্জ সমস্যা?", reply_markup=recharge_menu())
    elif text == "🚗 Drive Problem":
        bot.send_message(uid, "কোন অপারেটরে ড্রাইভ সমস্যা?", reply_markup=drive_menu())
    elif text == "☎️ সহযোগিতা (Support)":
        bot.send_message(uid, "<b>👋 এডমিন সাপোর্ট:</b>\nবিস্তারিত লিখে পাঠান বা স্ক্রিনশট দিন।", parse_mode="HTML")
    elif text == "🏠 মেইন মেনু":
        start(message)
    
    # সাব-বাটন রেসপন্স
    elif text and ("Recharge" in text):
        bot.send_message(uid, f"আপনি <b>{text}</b> সিলেক্ট করেছেন।\n\n✅ <b>SRM TELECOM</b> এর হিস্টোরি থেকে স্ক্রিনশট এবং রিচার্জ নম্বরটি লিখে পাঠান।", parse_mode="HTML")
    elif text and ("Drive" in text):
        bot.send_message(uid, f"আপনি <b>{text}</b> সিলেক্ট করেছেন।\n\n✅ <b>SRM TELECOM</b> এর স্ক্রিনশট + আপনার সিমের <b>My Operator App</b> এর স্ক্রিনশট এবং নম্বরটি দিন।", parse_mode="HTML")
    elif text in ["Bkash Personal", "Nagad Personal", "Upay Personal", "Bkash Agent", "Nagad Agent"]:
        bot.send_message(uid, f"আপনি <b>{text}</b> সিলেক্ট করেছেন।\nস্ক্রিনশট এবং ট্রানজেকশন আইডি দিন।", parse_mode="HTML")

    # ফরওয়ার্ডিং সিস্টেম (ইউজার যখন কিছু পাঠাবে)
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            try:
                bot.forward_message(admin, message.chat.id, message.message_id)
                bot.send_message(admin, f"📩 <b>নতুন বার্তা</b>\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
            except: pass
        bot.send_message(uid, "✅ আপনার মেসেজ এডমিনকে জানানো হয়েছে।")

# এডমিন রিপ্লাই লজিক
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def reply_logic(message):
    try:
        reply_info = message.reply_to_message.text or message.reply_to_message.caption
        target_id = reply_info.split("🆔 ID:")[1].strip().split("\n")[0]
        
        if message.content_type == 'text':
            bot.send_message(target_id, f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.text}", parse_mode="HTML")
        elif message.content_type == 'photo':
            bot.send_photo(target_id, message.photo[-1].file_id, caption=f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.caption if message.caption else ''}", parse_mode="HTML")
        bot.reply_to(message, "✅ পাঠানো হয়েছে।")
    except:
        bot.reply_to(message, "❌ আইডি পাওয়া যায়নি।")

# --- বট স্টার্ট ---
if __name__ == "__main__":
    # থ্রেডিং ব্যবহার করে ফ্ল্যাঙ্ক এবং বট একসাথে চালানো
    t = threading.Thread(target=run_web)
    t.start()
    bot.infinity_polling()
