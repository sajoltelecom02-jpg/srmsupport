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

# --- ডাটা লোড ও সেভ ---
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
    "📲 Apps link": {"text": "<b>📥 অ্যাপ লিঙ্ক:</b>\nhttps://play.google.com/store/apps/details?id=com.shuvotelecom24.user"},
    "💰 Add balance problem": {"text": "<b>💸 ব্যালেন্স সমস্যা?</b>\nট্রানজেকশন আইডি দিন।"}
})

# --- হেল্পার ফাংশন ---
def is_joined(user_id):
    if user_id in ADMINS: return True
    try:
        ch = bot.get_chat_member(MY_CHANNEL_ID, user_id).status
        gr = bot.get_chat_member(MY_GROUP_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return ch in allowed and gr in allowed
    except: return False

def main_menu(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btns = [telebot.types.KeyboardButton(b) for b in dynamic_buttons.keys()]
    markup.add(*btns)
    if user_id in ADMINS: markup.add("⚙️ Admin Panel")
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
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📞 নম্বর শেয়ার", request_contact=True))
        bot.send_message(uid, "👋 কাজ শুরু করতে নম্বর শেয়ার করুন।", reply_markup=markup)
    elif not users[uid]["loc"]:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📍 লোকেশন শেয়ার", request_location=True))
        bot.send_message(uid, "📍 এবার লোকেশন শেয়ার করুন।", reply_markup=markup)
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
    if message.contact: users[uid]["phone"] = message.contact.phone_number
    if message.location: users[uid]["loc"] = f"{message.location.latitude},{message.location.longitude}"
    save_data(DATA_FILE, users)
    start(message)

# --- এডমিন বাটন ম্যানেজমেন্ট ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "➕ বাটন অ্যাড")
def add_btn_start(message):
    msg = bot.send_message(message.chat.id, "নতুন বাটনের নাম দিন:", reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, add_btn_reply)

def add_btn_reply(message):
    name = message.text
    msg = bot.send_message(message.chat.id, f"'{name}' এর রিপ্লাই লিখুন:")
    bot.register_next_step_handler(msg, lambda m: finalize_add(m, name))

def finalize_add(message, name):
    dynamic_buttons[name] = {"text": message.text}
    save_data(BUTTONS_FILE, dynamic_buttons)
    bot.send_message(message.chat.id, f"✅ '{name}' বাটন অ্যাড হয়েছে!", reply_markup=main_menu(message.chat.id))

@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.text == "❌ বাটন ডিলিট")
def del_btn_start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for b in dynamic_buttons.keys(): markup.add(b)
    markup.add("🏠 মেইন মেনু")
    msg = bot.send_message(message.chat.id, "কোনটি ডিলিট করবেন?", reply_markup=markup)
    bot.register_next_step_handler(msg, finalize_del)

def finalize_del(message):
    if message.text in dynamic_buttons:
        del dynamic_buttons[message.text]
        save_data(BUTTONS_FILE, dynamic_buttons)
        bot.send_message(message.chat.id, "✅ ডিলিট সফল!", reply_markup=main_menu(message.chat.id))
    else: start(message)

# --- রিপ্লাই লজিক ---
@bot.message_handler(func=lambda m: m.chat.id in ADMINS and m.reply_to_message is not None)
def admin_reply(message):
    try:
        reply_info = message.reply_to_message.text if message.reply_to_message.text else message.reply_to_message.caption
        target_id = reply_info.split("🆔 ID:")[1].strip().split("\n")[0]
        bot.send_message(target_id, f"✉️ <b>এডমিন:</b> {message.text}", parse_mode="HTML")
        bot.reply_to(message, "✅ রিপ্লাই পাঠানো হয়েছে।")
    except:
        bot.reply_to(message, "❌ আইডি পাওয়া যায়নি।")

# --- গ্লোবাল হ্যান্ডলার ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    uid = str(message.chat.id)
    if not is_joined(message.chat.id): start(message); return

    if message.text in dynamic_buttons:
        bot.send_message(uid, dynamic_buttons[message.text]["text"], parse_mode="HTML")
    elif message.text == "⚙️ Admin Panel" and message.chat.id in ADMINS:
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add("➕ বাটন অ্যাড", "❌ বাটন ডিলিট")
        markup.add("🏠 মেইন মেনু")
        bot.send_message(message.chat.id, "🛠 এডমিন মেনু:", reply_markup=markup)
    elif message.text == "🏠 মেইন মেনু": start(message)
    elif message.chat.id not in ADMINS:
        for admin in ADMINS:
            bot.forward_message(admin, message.chat.id, message.message_id)
            bot.send_message(admin, f"📩 <b>নতুন বার্তা</b>\n🆔 ID: <code>{uid}</code>\n(রিপ্লাই দিতে এটি ব্যবহার করুন)", parse_mode="HTML")
        bot.send_message(uid, "✅ এডমিনকে জানানো হয়েছে।")

bot.infinity_polling()
