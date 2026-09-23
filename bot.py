
import time
import telebot
from telebot import types
from pymongo import MongoClient

# ==================================================
# BOT SETTINGS & DATABASE
# ==================================================

# @BotFather से मिला अपना बॉट टोकन यहाँ डालें
BOT_TOKEN = "8223193789:AAF0tR9P14igTuaGvKjKIzigEfzJLJ1ER6I"

# अपना Telegram numeric ID यहाँ डालें (उदा. 123456789)
ADMIN_ID = 6278812118

# आपका MongoDB Connection URL (पासवर्ड सेट है)
MONGO_URI = "mongodb+srv://ramlakhankushwaha9977_db_user:RamPass2026@cluster0.93sn40m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB कनेक्ट करें
client = MongoClient(MONGO_URI)
db = client["telegram_bot_db"]
posts_collection = db["posts"]

# ==================================================
# BOT INITIALIZATION
# ==================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
states = {}

# ==================================================
# LOAD & SAVE POSTS (MONGODB)
# ==================================================

def load_posts():
    try:
        # डेटाबेस से सभी पोस्ट्स निकालें
        posts = list(posts_collection.find({}, {"_id": 0}))
        return posts
    except Exception as e:
        print("Database fetch error:", e)
        return []

def save_post_to_db(post):
    try:
        # डेटाबेस में नई पोस्ट डालें
        posts_collection.insert_one(post)
        return True
    except Exception as e:
        print("Database save error:", e)
        return False

# ==================================================
# ADMIN CHECK
# ==================================================

def is_admin(message):
    return message.from_user.id == ADMIN_ID

# ==================================================
# CREATE BUTTONS
# ==================================================

def create_buttons(posts, index):
    keyboard = types.InlineKeyboardMarkup()

    # Next Video Button
    if index + 1 < len(posts):
        keyboard.add(
            types.InlineKeyboardButton(
                "🎬 Next Video",
                callback_data=f"next_{index + 1}"
            )
        )
    else:
        keyboard.add(
            types.InlineKeyboardButton(
                "❌ No Video Available",
                callback_data="no_video"
            )
        )

    # Daily Earning Channel Button
    keyboard.add(
        types.InlineKeyboardButton(
            "💰 Daily Earning Channel",
            url=posts[index]["channel_link"]
        )
    )

    return keyboard

# ==================================================
# SEND POST
# ==================================================

def send_post(chat_id, index):
    posts = load_posts()

    if not posts or index >= len(posts):
        bot.send_message(chat_id, "❌ <b>No Video Available</b>")
        return

    post = posts[index]

    caption = (
        "🎬 <b>Vdo 😍</b>\n\n"
        "🔗 <b>यह रहा वीडियो लिंक 👇</b>\n"
        f"{post['video_link']}\n\n"
        "😉 <b>Daily Trending. Open 👇</b>"
    )

    keyboard = create_buttons(posts, index)

    if post["type"] == "photo":
        bot.send_photo(
            chat_id=chat_id,
            photo=post["file_id"],
            caption=caption,
            reply_markup=keyboard
        )
    elif post["type"] == "video":
        bot.send_video(
            chat_id=chat_id,
            video=post["file_id"],
            caption=caption,
            reply_markup=keyboard
        )

# ==================================================
# /MYID
# ==================================================

@bot.message_handler(commands=["myid"])
def myid(message):
    bot.reply_to(
        message,
        f"🆔 <b>Your Telegram ID:</b>\n\n<code>{message.from_user.id}</code>"
    )

# ==================================================
# /START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):
    posts = load_posts()

    if not posts:
        bot.reply_to(
            message,
            "👋 <b>Welcome!</b>\n\n❌ अभी कोई video available नहीं है।"
        )
        return

    send_post(message.chat.id, 0)

# ==================================================
# NEXT VIDEO BUTTON CALLBACK
# ==================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("next_"))
def next_video(call):
    try:
        index = int(call.data.split("_")[1])
    except:
        bot.answer_callback_query(call.id, "❌ Invalid video.")
        return

    posts = load_posts()

    if index >= len(posts):
        bot.answer_callback_query(call.id, "❌ No Video Available")
        bot.send_message(call.message.chat.id, "❌ <b>No Video Available</b>")
        return

    bot.answer_callback_query(call.id)
    send_post(call.message.chat.id, index)

# ==================================================
# NO VIDEO BUTTON CALLBACK
# ==================================================

@bot.callback_query_handler(func=lambda call: call.data == "no_video")
def no_video_click(call):
    bot.answer_callback_query(call.id, "❌ No Video Available")

# ==================================================
# /ADDPOST (POST ADDING PROCESS)
# ==================================================

@bot.message_handler(commands=["addpost"])
def addpost(message):
    if not is_admin(message):
        bot.reply_to(
            message,
            "❌ <b>Access Denied</b>\n\nआपको /addpost की permission नहीं है।"
        )
        return

    states[message.chat.id] = {"step": "media"}

    bot.reply_to(
        message,
        "📸 <b>Step 1/3</b>\n\nअब Photo या Video भेजें।"
    )

@bot.message_handler(content_types=["photo", "video"])
def receive_media(message):
    chat_id = message.chat.id

    if chat_id not in states or states[chat_id].get("step") != "media":
        return

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        media_type = "photo"
    else:
        file_id = message.video.file_id
        media_type = "video"

    states[chat_id]["file_id"] = file_id
    states[chat_id]["type"] = media_type
    states[chat_id]["step"] = "video_link"

    bot.reply_to(
        message,
        "✅ <b>Media received!</b>\n\n🔗 <b>Step 2/3</b>\n\nअब Main Video Link भेजें:"
    )

@bot.message_handler(func=lambda msg: msg.chat.id in states and states[msg.chat.id].get("step") == "video_link")
def receive_video_link(message):
    states[message.chat.id]["video_link"] = message.text
    states[message.chat.id]["step"] = "channel"

    bot.reply_to(
        message,
        "💰 <b>Step 3/3</b>\n\nअब Daily Earning Channel का Link भेजें:"
    )

@bot.message_handler(func=lambda msg: msg.chat.id in states and states[msg.chat.id].get("step") == "channel")
def receive_channel(message):
    chat_id = message.chat.id

    new_post = {
        "type": states[chat_id]["type"],
        "file_id": states[chat_id]["file_id"],
        "video_link": states[chat_id]["video_link"],
        "channel_link": message.text
    }

    # सीधे MongoDB डेटाबेस में सेव करें
    save_post_to_db(new_post)
    total_count = posts_collection.count_documents({})

    del states[chat_id]

    bot.reply_to(
        message,
        f"✅ <b>Post Successfully Saved in Database!</b>\n\n"
        f"🎬 Total Videos: <b>{total_count}</b>\n\n"
        "अब /start करने पर पहली video आएगी।\n"
        "Next Video दबाने पर अगली video आएगी।"
    )

@bot.message_handler(commands=["cancel"])
def cancel(message):
    chat_id = message.chat.id
    if chat_id in states:
        del states[chat_id]
    bot.reply_to(message, "❌ <b>Post creation cancelled.</b>")

# ==================================================
# START BOT
# ==================================================

print("🤖 Bot Started with MongoDB...")

while True:
    try:
        bot.infinity_polling(
            timeout=20,
            long_polling_timeout=20,
            skip_pending=True
        )
    except Exception as e:
        print("⚠️ Connection error:", e)
        time.sleep(3)
