import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from moviepy.editor import VideoFileClip
import asyncio
from flask import Flask
import threading

# Flask server
app = Flask(__name__)

@app.route('/health')
def health():
    return "OK", 200

# Til sozlamalari
LANGUAGES = {
    "en": {
        "choose_lang": "Choose language:",
        "processing": "Processing your video...",
        "send_video": "Send me a video!"
    },
    "ru": {
        "choose_lang": "Выберите язык:",
        "processing": "Обработка видео...",
        "send_video": "Отправьте мне видео!"
    },
    "uz": {
        "choose_lang": "Tilni tanlang:",
        "processing": "Videoni qayta ishlash...",
        "send_video": "Menga video yuboring!"
    }
}

# JSON faylni yuklash/saqlash
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# Tilni o'rnatish (komanda orqali)
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_users()
    lang_code = context.args[0] if context.args else None
    if lang_code in LANGUAGES:
        users[user_id] = lang_code
        save_users(users)
        await update.message.reply_text(f"✅ Language set to {lang_code.upper()}")
    else:
        keyboard = [["🇺🇸 English", "🇷🇺 Русский", "🇺🇿 O'zbek"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("🌐 Choose your language:", reply_markup=reply_markup)

# Asosiy xabarlar uchun handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)
    users = load_users()

    lang_map = {
        "🇺🇸 English": "en",
        "🇷🇺 Русский": "ru",
        "🇺🇿 O'zbek": "uz"
    }

    # Til tanlash tugmalari
    if text in lang_map:
        users[user_id] = lang_map[text]
        save_users(users)
        lang = lang_map[text]
        await update.message.reply_text(LANGUAGES[lang]["send_video"])
        return

    # Agar video yuborilgan bo'lsa
    if update.message.video:
        lang = users.get(user_id, "en")
        await update.message.reply_text(LANGUAGES[lang]["processing"])
        await process_video(update, context, lang)
        return

    # Agar hech narsa yuborilmagan — faqat video so'raymiz
    lang = users.get(user_id, "en")
    await update.message.reply_text(f"📹 {LANGUAGES[lang]['send_video']}")

# Video qayta ishlash
async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    video_file = await update.message.video.get_file()
    input_path = f"{update.effective_user.id}_input.mp4"
    output_path = f"{update.effective_user.id}_output.mp4"

    try:
        await video_file.download_to_drive(input_path)

        clip = VideoFileClip(input_path)
        
        # 10 daqiqaga cheklash (600 soniya)
        if clip.duration > 600:
            clip = clip.subclip(0, 600)

        # Kvadrat formatga keltirish (markazdan kesish)
        w, h = clip.size
        size = min(w, h)
        clip = clip.crop(
            x_center=w/2,
            y_center=h/2,
            width=size,
            height=size
        )

        # Natijani saqlash
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close()

        # Yuborish
        with open(output_path, "rb") as video:
            await update.message.reply_video(video=video, supports_streaming=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    finally:
        # Fayllarni tozalash
        for f in [input_path, output_path]:
            if os.path.exists(f):
                os.remove(f)

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context)

# Asosiy dastur
def main():
    application = Application.builder().token("8313385612:AAFnjk6xyV6a_4l9OSf9MFm5WZjsguWyY5E").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", set_language))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_message))

    print("✅ Bot ishga tushdi. /start buyrug'ini yuboring.")
    application.run_polling()

# Flask serverni alohida threadda ishga tushirish
def start_flask():
    app.run(host='0.0.0.0', port=8080, threaded=True)

if __name__ == "__main__":
    # Flask serverni alohida threadda ishga tushirish
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Botni ishga tushirish
    main()