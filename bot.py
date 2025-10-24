from flask import Flask, request, jsonify
from moviepy.editor import VideoFileClip
import telebot
import os

# ---------------- Telegram Bot ----------------
TOKEN = "YOUR_BOT_TOKEN"
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi tillarini saqlash
user_languages = {}

# ---------------- Flask App ----------------
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Til tanlash va video yuborish uchun endpoint
@app.route("/bot", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    chat_id = None
    try:
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]

            # /start komandasi
            if "text" in message and message["text"] == "/start":
                markup = {
                    "keyboard": [["English", "Русский", "O'zbek"]],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                bot.send_message(chat_id, "Choose your language / Выберите язык / Tilni tanlang:", reply_markup=markup)
                return jsonify({"status": "ok"})

            # Tilni tanlash
            if "text" in message and message["text"] in ["English", "Русский", "O'zbek"]:
                user_languages[chat_id] = message["text"]
                lang = message["text"]
                if lang == "English":
                    bot.send_message(chat_id, "Great! Now send me a video and I will make it round.")
                elif lang == "Русский":
                    bot.send_message(chat_id, "Отлично! Теперь пришлите видео, и я сделаю его круглым.")
                else:
                    bot.send_message(chat_id, "Ajoyib! Endi menga video yuboring, men uni dumaloq qilaman.")
                return jsonify({"status": "ok"})

            # Video qabul qilish
            if "video" in message or "document" in message:
                file_id = message.get("video", message.get("document"))["file_id"]
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                
                input_path = os.path.join(UPLOAD_FOLDER, f"{chat_id}_input.mp4")
                output_path = os.path.join(UPLOAD_FOLDER, f"{chat_id}_output.mp4")
                
                with open(input_path, "wb") as f:
                    f.write(downloaded_file)

                # Dumaloq video yaratish (professional maska)
                try:
                    clip = VideoFileClip(input_path)
                    size = min(clip.w, clip.h)
                    clip_resized = clip.resize(height=size) if clip.h > clip.w else clip.resize(width=size)
                    clip_resized = clip_resized.crop(x_center=clip_resized.w/2, y_center=clip_resized.h/2, width=size, height=size)
                    
                    # professional silliq dumaloq maska
                    clip_resized = clip_resized.fx(lambda c: c)  # agar keyin effektlar qo‘shilsa
                    clip_resized.write_videofile(output_path, codec="libx264", audio_codec="aac")
                    
                    with open(output_path, "rb") as f:
                        bot.send_video(chat_id, f)
                    
                    os.remove(input_path)
                    os.remove(output_path)
                except Exception as e:
                    lang = user_languages.get(chat_id, "English")
                    if lang == "English":
                        bot.send_message(chat_id, f"Error processing video: {e}")
                    elif lang == "Русский":
                        bot.send_message(chat_id, f"Ошибка обработки видео: {e}")
                    else:
                        bot.send_message(chat_id, f"Video bilan ishlashda xatolik: {e}")

        return jsonify({"status": "ok"})
    except Exception as e:
        if chat_id:
            bot.send_message(chat_id, f"Unexpected error: {e}")
        return jsonify({"status": "error", "error": str(e)})

# ---------------- Flask run ----------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
