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

# --- ডাটাবেস হ্যান্ডলিং ---
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if data else default
        except:
            return default
    return default

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- মেনু জেনারেটর ---
def main_menu(user_id):
    btns = load_data(BUTTONS_FILE, {
        "📲 Apps link": "📥 লিঙ্ক: https://play.google.com/store/apps/details?id=com.shuvotelecom24.user",
        "💰 Balance Problem": "ব্যালেন্স সমস্যা? স্ক্রিনশট দিন।"
    })
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for b_name in btns.keys():
        markup.add(telebot.types.KeyboardButton(b_name))
    if user_id in ADMINS:
        markup.add(telebot.types.KeyboardButton("⚙️ Admin Panel"))
    return markup

def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        return ch in ['member', 'administrator', 'creator'] and gr in ['member', 'administrator', 'creator']
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
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📞 নম্বর শেয়ার", request_contact=True))
        bot.send_message(uid, "👋 কাজ শুরু করতে আপনার নম্বরটি শেয়ার করুন।", reply_markup=markup)
    elif not users[uid].get("loc"):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📍 লোকেশন শেয়ার", request_location=True))
        bot.send_message(uid, "📍 এবার আপনার লোকেশনটি শেয়ার করুন।", reply_markup=markup)
    else:
        bot.send_message(uid, "🌟 <b>S.R.M TELECOM</b>", reply_markup=main_menu(message.chat.id), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_joined(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
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

# --- এডমিন প্যানেল ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "⚙️ Admin Panel")
def admin_p(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ বাটন অ্যাড", "❌ বাটন ডিলিট", "🏠 মেইন মেনু")
    bot.send_message(message.chat.id, "🛠 এডমিন প্যানেল:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "➕ বাটন অ্যাড")
def add_btn_1(message):
    msg = bot.send_message(message.chat.id, "বাটনের নাম কী হবে?", reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, add_btn_2)

def add_btn_2(message):
    name = message.text
    msg = bot.send_message(message.chat.id, f"'{name}' এর রিপ্লাই কী হবে?")
    bot.register_next_step_handler(msg, lambda m: finalize_add(m, name))

def finalize_add(message, name):
    btns = load_data(BUTTONS_FILE, {})
    btns[name] = message.text
    save_data(BUTTONS_FILE, btns)
    bot.send_message(message.chat.id, "✅ অ্যাড হয়েছে!", reply_markup=admin_p(message))

@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "❌ বাটন ডিলিট")
def del_btn_1(message):
    btns = load_data(BUTTONS_FILE, {})
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for b in btns.keys(): markup.add(b)
    markup.add("🏠 মেইন মেনু")
    msg = bot.send_message(message.chat.id, "কোনটি ডিলিট করবেন?", reply_markup=markup)
    bot.register_next_step_handler(msg, finalize_del)

def finalize_del(message):
    btns = load_data(BUTTONS_FILE, {})
    if message.text in btns:
        del btns[message.text]
        save_data(BUTTONS_FILE, btns)
        bot.send_message(message.chat.id, "✅ ডিলিট হয়েছে।", reply_markup=main_menu(message.chat.id))
    else: start(message)

# --- গ্লোবাল মেসেজ ও রিপ্লাই ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    btns = load_data(BUTTONS_FILE, {})

    if message.text in btns:
        bot.send_message(uid, btns[message.text], parse_mode="HTML")
    elif message.text == "🏠 মেইন মেনু":
        start(message)
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            bot.forward_message(admin, message.chat.id, message.message_id)
            bot.send_message(admin, f"📩 <b>নতুন বার্তা</b>\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")
        bot.send_message(uid, "✅ এডমিনকে জানানো হয়েছে।")

@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message)
def reply_logic(message):
    try:
        reply_text = message.reply_to_message.text or message.reply_to_message.caption
        target_id = reply_text.split("🆔 ID:")[1].strip()
        bot.send_message(target_id, f"✉️ <b>এডমিন রিপ্লাই:</b>\n\n{message.text}", parse_mode="HTML")
        bot.reply_to(message, "✅ পাঠানো হয়েছে।")
    except: pass

bot.infinity_polling()
