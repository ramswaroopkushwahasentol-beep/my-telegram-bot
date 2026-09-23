import telebot
import json
import os
import time

from telebot import types


# ==================================================
# BOT SETTINGS
# ==================================================

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# अपना Telegram numeric ID यहाँ डालें
ADMIN_ID = 123456789


# ==================================================
# FILE
# ==================================================

DATA_FILE = "posts.json"


# ==================================================
# BOT
# ==================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ==================================================
# TEMPORARY USER STATES
# ==================================================

states = {}


# ==================================================
# LOAD POSTS
# ==================================================

def load_posts():

    if not os.path.exists(DATA_FILE):
        return []

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, list):
                return data

            return []

    except Exception as e:

        print("Post file error:", e)

        return []


# ==================================================
# SAVE POSTS
# ==================================================

def save_posts(posts):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            posts,
            f,
            ensure_ascii=False,
            indent=2
        )


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

    # ------------------------------
    # NEXT VIDEO
    # ------------------------------

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

    # ------------------------------
    # DAILY EARNING
    # ------------------------------

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

    # कोई post नहीं है
    if not posts:

        bot.send_message(
            chat_id,
            "❌ <b>No Video Available</b>"
        )

        return


    # अगर index गलत है
    if index >= len(posts):

        bot.send_message(
            chat_id,
            "❌ <b>No Video Available</b>"
        )

        return


    post = posts[index]


    caption = (
        "🎬 <b>Vdo 😍</b>\n\n"

        "🔗 <b>यह रहा वीडियो लिंक 👇</b>\n"
        f"{post['video_link']}\n\n"

        "😉 <b>Daily Trending. Open 👇</b>"
    )


    keyboard = create_buttons(
        posts,
        index
    )


    # PHOTO
    if post["type"] == "photo":

        bot.send_photo(
            chat_id=chat_id,
            photo=post["file_id"],
            caption=caption,
            reply_markup=keyboard
        )


    # VIDEO
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

        "🆔 <b>Your Telegram ID:</b>\n\n"
        f"<code>{message.from_user.id}</code>"
    )


# ==================================================
# /START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    print(
        f"/start received from "
        f"{message.from_user.id}"
    )

    posts = load_posts()


    if not posts:

        bot.reply_to(
            message,

            "👋 <b>Welcome!</b>\n\n"
            "❌ अभी कोई video available नहीं है।"
        )

        return


    # पहली video
    send_post(
        message.chat.id,
        0
    )


# ==================================================
# NEXT VIDEO BUTTON
# ==================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("next_")
)
def next_video(call):

    try:

        index = int(
            call.data.split("_")[1]
        )

    except:

        bot.answer_callback_query(
            call.id,
            "❌ Invalid video."
        )

        return


    posts = load_posts()


    # अब कोई अगली video नहीं
    if index >= len(posts):

        bot.answer_callback_query(
            call.id,
            "❌ No Video Available"
        )

        bot.send_message(
            call.message.chat.id,
            "❌ <b>No Video Available</b>"
        )

        return


    bot.answer_callback_query(
        call.id
    )


    # अगली uploaded video भेजें
    send_post(
        call.message.chat.id,
        index
    )


# ==================================================
# NO VIDEO BUTTON
# ==================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "no_video"
)
def no_video(call):

    bot.answer_callback_query(
        call.id,
        "❌ No Video Available"
    )


# ==================================================
# /ADDPOST
# ==================================================

@bot.message_handler(commands=["addpost"])
def addpost(message):

    if not is_admin(message):

        bot.reply_to(
            message,

            "❌ <b>Access Denied</b>\n\n"
            "आपको /addpost की permission नहीं है।"
        )

        return


    states[message.chat.id] = {
        "step": "media"
    }


    bot.reply_to(
        message,

        "📸 <b>Step 1/3</b>\n\n"
        "अब Photo या Video भेजें।"
    )


# ==================================================
# RECEIVE PHOTO / VIDEO
# ==================================================

@bot.message_handler(
    content_types=[
        "photo",
        "video"
    ]
)
def receive_media(message):

    chat_id = message.chat.id


    if chat_id not in states:
        return


    if states[chat_id]["step"] != "media":
        return


    # PHOTO
    if message.content_type == "photo":

        file_id = message.photo[-1].file_id

        media_type = "photo"


    # VIDEO
    else:

        file_id = message.video.file_id

        media_type = "video"


    states[chat_id]["file_id"] = file_id

    states[chat_id]["type"] = media_type

    states[chat_id]["step"] = "video_link"


    bot.reply_to(
        message,

        "✅ <b>Media received!</b>\n\n"

        "🔗 <b>Step 2/3</b>\n\n"

        "अब Main Video Link भेजें:"
    )


# ==================================================
# VIDEO LINK
# ==================================================

@bot.message_handler(
    func=lambda message:
    message.chat.id in states
    and states[message.chat.id]["step"]
    == "video_link"
)
def receive_video_link(message):

    states[
        message.chat.id
    ]["video_link"] = message.text

    states[
        message.chat.id
    ]["step"] = "channel"


    bot.reply_to(
        message,

        "💰 <b>Step 3/3</b>\n\n"

        "अब Daily Earning Channel का Link भेजें:"
    )


# ==================================================
# CHANNEL LINK
# ==================================================

@bot.message_handler(
    func=lambda message:
    message.chat.id in states
    and states[message.chat.id]["step"]
    == "channel"
)
def receive_channel(message):

    chat_id = message.chat.id


    new_post = {

        "type":
        states[chat_id]["type"],

        "file_id":
        states[chat_id]["file_id"],

        "video_link":
        states[chat_id]["video_link"],

        "channel_link":
        message.text
    }


    # पुराने posts लाओ
    posts = load_posts()


    # नई video list के आखिर में जोड़ो
    posts.append(new_post)


    # Save
    save_posts(posts)


    # State clear
    del states[chat_id]


    bot.reply_to(
        message,

        "✅ <b>Post Successfully Saved!</b>\n\n"

        f"🎬 Total Videos: <b>{len(posts)}</b>\n\n"

        "अब /start करने पर पहली video आएगी।\n"
        "Next Video दबाने पर अगली uploaded video आएगी।"
    )


# ==================================================
# /CANCEL
# ==================================================

@bot.message_handler(commands=["cancel"])
def cancel(message):

    chat_id = message.chat.id


    if chat_id in states:

        del states[chat_id]


    bot.reply_to(
        message,

        "❌ <b>Post creation cancelled.</b>"
    )


# ==================================================
# START BOT
# ==================================================

print("🤖 Bot Started...")
print("⚡ Waiting for messages...")


while True:

    try:

        bot.infinity_polling(
            timeout=20,
            long_polling_timeout=20,
            skip_pending=True
        )

    except Exception as e:

        print(
            "⚠️ Connection error:",
            e
        )

        print(
            "🔄 Reconnecting in 3 seconds..."
        )

        time.sleep(3)
