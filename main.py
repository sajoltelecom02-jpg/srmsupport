import telebot
import json
import os

# --- কনফিগারেশন ---
TOKEN = "8760273912:AAF-y04Ntoz2QB49h6zMiaPardMFtfUSAk8"
ADMINS = [5788640897]
MY_CHANNEL_ID = -1002323081321  
MY_GROUP_ID = -1002011910940    
DATA_FILE = "users.json"
BUTTONS_FILE = "buttons.json"

bot = telebot.TeleBot(TOKEN)

# --- ডাটাবেস হ্যান্ডলিং (ফাইল সিস্টেম) ---
def load_data(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return default
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

users = load_data(DATA_FILE, {})
dynamic_buttons = load_data(BUTTONS_FILE, {
    "📲 Apps link": {"text": "<b>📥 অ্যাপ লিঙ্ক:</b>\nhttps://play.google.com/store/apps/details?id=com.shuvotelecom24.user", "sub": {}},
    "💰 Add balance problem": {"text": "<b>💸 ব্যালেন্স সমস্যা?</b>\nআপনার ট্রানজেকশন আইডি দিন।", "sub": {}},
    "🌐 Website link": {"text": "https://srmtelecom.xyz", "sub": {}}
})

# --- হেল্পার ফাংশনস ---
def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        return ch in ['member', 'administrator', 'creator'] and gr in ['member', 'administrator', 'creator']
    except: return False

def main_menu(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btns = [telebot.types.KeyboardButton(b) for b in dynamic_buttons.keys()]
    markup.add(*btns)
    if user_id in ADMINS: markup.add("⚙️ Admin Panel")
    return markup

def admin_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("➕ বাটন অ্যাড", "❌ বাটন ডিলিট")
    markup.add("📋 ইউজার লিস্ট", "🏠 মেইন মেনু")
    return markup

# --- স্টার্ট ফ্লো ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    if uid not in users:
        users[uid] = {"name": message.from_user.first_name, "phone": None, "loc": None}
        save_data(DATA_FILE, users)

    if not is_joined(message.chat.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 Channel", url="https://t.me/srmtelecom"),
                   telebot.types.InlineKeyboardButton("👥 Group", url="https://t.me/sajoltelecom2"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I join", callback_data="check_join"))
        bot.send_message(uid, "<b>⚠️ জয়েন বাধ্যতামূলক!</b>", reply_markup=markup, parse_mode="HTML")
        return

    if not users[uid]["phone"]:
        bot.send_message(uid, "📞 নম্বর শেয়ার করুন:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📞 নম্বর শেয়ার", request_contact=True)))
    elif not users[uid]["loc"]:
        bot.send_message(uid, "📍 লোকেশন শেয়ার করুন:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton("📍 লোকেশন শেয়ার", request_location=True)))
    else:
        bot.send_message(uid, f"🌟 <b>S.R.M TELECOM</b>\nস্বাগতম {message.from_user.first_name}!", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def cb_join(call):
    if is_joined(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "আগে ঠিকভাবে জয়েন করুন! 😡", show_alert=True)

# --- ডাটা সংগ্রহ ---
@bot.message_handler(content_types=['contact', 'location'])
def data_collect(message):
    uid = str(message.chat.id)
    if message.contact: users[uid]["phone"] = message.contact.phone_number
    if message.location: users[uid]["loc"] = f"{message.location.latitude},{message.location.longitude}"
    save_data(DATA_FILE, users)
    start(message)

# --- এডমিন বাটন ম্যানেজমেন্ট ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "➕ বাটন অ্যাড")
def add_btn(message):
    msg = bot.send_message(message.chat.id, "বাটনের নাম দিন:", reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, add_btn_reply)

def add_btn_reply(message):
    name = message.text
    msg = bot.send_message(message.chat.id, f"'{name}' এর রিপ্লাই লিখুন:")
    bot.register_next_step_handler(msg, lambda m: finalize_btn(m, name))

def finalize_btn(message, name):
    dynamic_buttons[name] = {"text": message.text, "sub": {}}
    save_data(BUTTONS_FILE, dynamic_buttons)
    bot.send_message(message.chat.id, "✅ বাটন সেভ হয়েছে!", reply_markup=admin_menu())

# --- গ্লোবাল হ্যান্ডলার ও রিপ্লাই ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    if not is_joined(message.chat.id): start(message); return

    if message.text in dynamic_buttons:
        bot.send_message(uid, dynamic_buttons[message.text]["text"], parse_mode="HTML")
    elif message.text == "⚙️ Admin Panel" and message.chat.id in ADMINS:
        bot.send_message(message.chat.id, "🛠 এডমিন মেনু:", reply_markup=admin_menu())
    elif message.text == "🏠 মেইন মেনু": start(message)
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            bot.forward_message(admin, message.chat.id, message.message_id)
            bot.send_message(admin, f"📩 🆔 ID: <code>{uid}</code>\n(Reply to answer)")
        bot.send_message(uid, "✅ মেসেজ পাঠানো হয়েছে।")

# রিপ্লাই লজিক
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message is not None)
def admin_reply(message):
    try:
        reply_info = message.reply_to_message.text if message.reply_to_message.text else message.reply_to_message.caption
        target_id = reply_info.split("🆔 ID:")[1].strip().split("\n")[0]
        bot.send_message(target_id, f"✉️ <b>এডমিন:</b> {message.text}", parse_mode="HTML")
        bot.reply_to(message, "✅ পাঠানো হয়েছে।")
    except: pass

bot.infinity_polling()

