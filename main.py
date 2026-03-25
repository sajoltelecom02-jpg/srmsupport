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

# --- Render Port Error Fix (Flask Server) ---
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

def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        return ch in ['member', 'administrator', 'creator'] and gr in ['member', 'administrator', 'creator']
    except: return False

# --- স্টার্ট কমান্ড ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
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
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        start(call.message)
    else: bot.answer_callback_query(call.id, "আগে ঠিকভাবে জয়েন করুন! 😡", show_alert=True)

# --- সমস্যা বর্ণনার ফ্লো ---
def ask_for_problem(message, sub_button_name):
    # সাব বাটন হাইড করে সমস্যা জানতে চাওয়া
    msg = bot.send_message(message.chat.id, f"আপনি <b>{sub_button_name}</b> সিলেক্ট করেছেন।\n\n✅ আপনার সমস্যাটি বিস্তারিত লিখে পাঠান (নম্বরসহ):", parse_mode="HTML", reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, lambda m: ask_for_screenshot(m, sub_button_name))

def ask_for_screenshot(message, sub_button_name):
    uid = str(message.chat.id)
    # ইউজারের লেখা সমস্যা এডমিনকে ফরওয়ার্ড করা
    for admin in ADMINS:
        bot.send_message(admin, f"📩 <b>নতুন রিপোর্ট ({sub_button_name})</b>\n👤 নাম: {message.from_user.first_name}\n📝 বর্ণনা: {message.text}\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
    
    bot.send_message(message.chat.id, "✅ আপনার সমস্যাটি নোট করা হয়েছে।\n\n📸 এবার প্রমাণের জন্য একটি <b>স্ক্রিনশট</b> পাঠান।", reply_markup=main_menu(message.chat.id))

# --- মেইন হ্যান্ডলার ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    text = message.text

    if text == "📲 Apps link":
        bot.send_message(uid, "<b>📥 অ্যাপ লিঙ্ক:</b>\nhttps://play.google.com/store/apps/details?id=com.shuvotelecom24.user", parse_mode="HTML")
    elif text == "💰 Balance Problem":
        bot.send_message(uid, "টাকা পাঠানোর মাধ্যম সিলেক্ট করুন:", reply_markup=balance_menu())
    elif text == "⚡ Recharge Problem":
        bot.send_message(uid, "অপারেটর সিলেক্ট করুন:", reply_markup=recharge_menu())
    elif text == "🚗 Drive Problem":
        bot.send_message(uid, "অপারেটর সিলেক্ট করুন:", reply_markup=drive_menu())
    elif text == "☎️ সহযোগিতা (Support)":
        bot.send_message(uid, "👋 সরাসরি এডমিনের সাথে কথা বলুন। সমস্যাটি লিখুন বা স্ক্রিনশট দিন।", parse_mode="HTML")
    elif text == "🏠 মেইন মেনু": start(message)

    # সাব-বাটন ক্লিক চেক (ব্যালেন্স, রিচার্জ, ড্রাইভ)
    elif text and ("Recharge" in text or "Drive" in text or "Personal" in text or "Agent" in text):
        ask_for_problem(message, text)
    
    # ফরওয়ার্ডিং (ইউজার যখন ফটো বা টেক্সট পাঠাবে)
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            try:
                bot.forward_message(admin, message.chat.id, message.message_id)
                bot.send_message(admin, f"📩 <b>নতুন বার্তা</b>\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
            except: pass
        bot.send_message(uid, "✅ এডমিনকে জানানো হয়েছে।")

# --- এডমিন রিপ্লাই ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def reply_logic(message):
    try:
        source_text = message.reply_to_message.text or message.reply_to_message.caption
        if source_text and "🆔 ID:" in source_text:
            target_id = source_text.split("🆔 ID:")[1].strip().split("\n")[0]
            if message.content_type == 'text':
                bot.send_message(target_id, f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.text}", parse_mode="HTML")
            elif message.content_type == 'photo':
                bot.send_photo(target_id, message.photo[-1].file_id, caption=f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.caption if message.caption else ''}", parse_mode="HTML")
            bot.reply_to(message, "✅ পাঠানো হয়েছে।")
    except: pass

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.infinity_polling()
