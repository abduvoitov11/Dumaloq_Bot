import json
import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import telebot
from flask import Flask
import threading

# Flask server (UptimeRobot uchun)
app = Flask(__name__)

@app.route('/health')
def health():
    return "OK", 200

# Til sozlamalari
LANGUAGES = {
    "en": {
        "welcome": "👋 Hi! Send me a video — I'll convert it to a circular video note 🔵🎥",
        "processing": "⏳ Processing your video...",
        "error": "❌ An error occurred: {}"
    },
    "ru": {
        "welcome": "👋 Привет! Отправьте мне видео — я преобразую его в круглое видео-заметку 🔵🎥",
        "processing": "⏳ Обработка видео...",
        "error": "❌ Произошла ошибка: {}"
    },
    "uz": {
        "welcome": "👋 Salom! Menga video yubor — men uni dumaloq video xabar (video note) qilib qaytaraman 🔵🎥",
        "processing": "⏳ Videoni qayta ishlash...",
        "error": "❌ Xatolik yuz berdi: {}"
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

# Tilni o'rnatish
def set_language(user_id, lang_code):
    users = load_users()
    users[str(user_id)] = lang_code
    save_users(users)

# Tilni olish
def get_language(user_id):
    users = load_users()
    return users.get(str(user_id), "uz")  # Default: O'zbek

# Bot tokeni
TOKEN = "8313385612:AAFnjk6xyV6a_4l9OSf9MFm5WZjsguWyY5E"
bot = telebot.TeleBot(TOKEN)

# Start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    lang = get_language(user_id)
    bot.reply_to(message, LANGUAGES[lang]["welcome"])

    # Til tanlash tugmalari
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_en = telebot.types.KeyboardButton("🇺🇸 English")
    button_ru = telebot.types.KeyboardButton("🇷🇺 Русский")
    button_uz = telebot.types.KeyboardButton("🇺🇿 O'zbek")
    keyboard.add(button_en, button_ru, button_uz)
    bot.send_message(message.chat.id, "🌐 Tilni tanlang:", reply_markup=keyboard)

# Til tanlash
@bot.message_handler(func=lambda message: message.text in ["🇺🇸 English", "🇷🇺 Русский", "🇺🇿 O'zbek"])
def handle_language(message):
    user_id = message.from_user.id
    lang_map = {
        "🇺🇸 English": "en",
        "🇷🇺 Русский": "ru",
        "🇺🇿 O'zbek": "uz"
    }
    lang_code = lang_map.get(message.text)
    if lang_code:
        set_language(user_id, lang_code)
        lang = get_language(user_id)
        bot.reply_to(message, f"✅ Til {lang_code.upper()} ga o'zgartirildi!")
        bot.send_message(message.chat.id, LANGUAGES[lang]["welcome"])

# Video qayta ishlash
@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    lang = get_language(user_id)

    try:
        bot.reply_to(message, LANGUAGES[lang]["processing"])

        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_path = f"{user_id}_input.mp4"
        output_path = f"{user_id}_circle.mp4"

        with open(input_path, "wb") as f:
            f.write(downloaded_file)

        # Videoni MoviePy orqali o‘qish
        clip = VideoFileClip(input_path).resize((400, 400))

        def make_circle_frame(frame):
            mask = np.zeros(frame.shape, dtype=np.uint8)
            h, w = frame.shape[:2]
            center = (w // 2, h // 2)
            radius = min(h, w) // 2
            cv2.circle(mask, center, radius, (255, 255, 255), -1)
            result = cv2.bitwise_and(frame, mask)
            return result

        new_clip = clip.fl_image(make_circle_frame)
        new_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)

        # Faylni qaytarish (video note formatida)
        with open(output_path, 'rb') as f:
            bot.send_video_note(message.chat.id, f)

        # Tozalash
        os.remove(input_path)
        os.remove(output_path)

    except Exception as e:
        bot.reply_to(message, LANGUAGES[lang]["error"].format(e))

# Flask serverni alohida threadda ishga tushirish
def start_flask():
    app.run(host='0.0.0.0', port=8080, threaded=True)

if __name__ == "__main__":
    # Flask serverni alohida threadda ishga tushirish
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Botni ishga tushirish
    print("🤖 Bot ishga tushdi...")
    bot.polling()