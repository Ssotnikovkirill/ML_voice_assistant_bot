# import os
# import ffmpeg
# import logging
# from telegram import Update
# from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
# from config import BOT_TOKEN, STAFF
# from staff import extract_names, find_best_match
# from utils import transcribe_audio, generate_direct_command

# from config import GMAIL_SENDER, GMAIL_PASSWORD
# from utils import send_gmail

# logging.basicConfig(level=logging.INFO)

# def start(update: Update, context: CallbackContext):
#     update.message.reply_text("Привет! Отправь голосовое сообщение с указанием имени сотрудника и задачей.")

# def handle_voice(update: Update, context: CallbackContext):
#     voice = update.message.voice.get_file()
#     ogg_path = "voice.ogg"
#     wav_path = "voice.wav"

#     voice.download(ogg_path)
#     ffmpeg.input(ogg_path).output(wav_path).run(overwrite_output=True)

#     text = transcribe_audio(wav_path)
#     names = extract_names(text)
#     match = find_best_match(names)

#     if not match:
#         update.message.reply_text("Не удалось найти сотрудника.")
#         return

#     command = generate_direct_command(text)
#     username = STAFF[match]["username"]
#     # Получаем список последних пользователей, писавших боту
#     chat_id = update.effective_chat.id
#     print(f"DEBUG: Отправка на chat_id={chat_id}")

#     # context.bot.send_message(chat_id=f"@{username}", text=command)
#     # context.bot.send_message(chat_id=chat_id, text=command)
#     # context.bot.send_message(chat_id=STAFF[match]["chat_id"], text=command)
#     context.bot.send_message(chat_id=update.effective_chat.id, text=command)
#     update.message.reply_text(f"Сообщение отправлено сотруднику @{username}:\n{command}")

#     os.remove(ogg_path)
#     os.remove(wav_path)

# def main():
#     updater = Updater(BOT_TOKEN)
#     dp = updater.dispatcher

#     dp.add_handler(CommandHandler("start", start))
#     dp.add_handler(MessageHandler(Filters.voice, handle_voice))

#     updater.start_polling()
#     updater.idle()

# if __name__ == "__main__":
#     main()

import csv
import os
import ffmpeg
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from config import BOT_TOKEN, STAFF, GMAIL_SENDER, GMAIL_PASSWORD
from staff import extract_names, find_best_match
from utils import transcribe_audio, generate_direct_command, send_gmail

logging.basicConfig(level=logging.INFO)

# def start(update: Update, context: CallbackContext):
#     update.message.reply_text("👋 Привет! Отправь голосовое сообщение с указанием имени сотрудника и задачей.")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Привет! Отправь голосовое сообщение с указанием имени сотрудника и задачей.")
    user = update.effective_user
    chat_id = update.effective_chat.id
    username = user.username or "нет username"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    # Сообщение пользователю
    # update.message.reply_text("👋 Привет! Ты зарегистрирован. Теперь я могу отправлять тебе сообщения.")

    # Проверим, не записан ли пользователь уже
    filename = "users.csv"
    already_registered = False

    if os.path.exists(filename):
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                if row and row[0] == str(chat_id):
                    already_registered = True
                    break

    # Если не зарегистрирован — добавим в файл
    if not already_registered:
        with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow([chat_id, username, full_name])
            print(f"✅ Новый пользователь: chat_id={chat_id}, @{username}, {full_name}")
    else:
        print(f"🔁 Пользователь уже зарегистрирован: chat_id={chat_id}, @{username}")


def handle_voice(update: Update, context: CallbackContext):
    voice = update.message.voice.get_file()
    ogg_path = "voice.ogg"
    wav_path = "voice.wav"

    # Сохраняем и конвертируем голосовое сообщение
    voice.download(ogg_path)
    ffmpeg.input(ogg_path).output(wav_path).run(overwrite_output=True)

    # Распознаем текст
    text = transcribe_audio(wav_path)
    names = extract_names(text)
    match = find_best_match(names)

    if not match:
        update.message.reply_text(" Не удалось найти сотрудника по голосовому сообщению.")
        os.remove(ogg_path)
        os.remove(wav_path)
        return

    command = generate_direct_command(text)
    staff_info = STAFF[match]

    # === Отправка в Telegram ===
    chat_id = staff_info.get("chat_id")
    if chat_id:
        try:
            context.bot.send_message(chat_id=chat_id, text=command)
            update.message.reply_text(f" Сообщение отправлено сотруднику @{staff_info['username']}:\n{command}")
        except Exception as e:
            update.message.reply_text(f" Ошибка отправки в Telegram: {str(e)}")
    else:
        update.message.reply_text(f" Не указан chat_id для сотрудника {match}.")

    # === Отправка на Email ===
    email = staff_info.get("email")
    if email:
        subject = command
        body = f"Здравствуйте, {match}!\n\n{command}\n\nС уважением,\nВаш голосовой ассистент."

        if send_gmail(GMAIL_SENDER, GMAIL_PASSWORD, email, subject, body):
            update.message.reply_text(f"📧 Email успешно отправлен на {email}.")
        else:
            update.message.reply_text(f" Не удалось отправить Email на {email}.")
    else:
        update.message.reply_text(f" Email сотрудника {match} не указан.")

    # Удаляем временные файлы
    os.remove(ogg_path)
    os.remove(wav_path)

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.voice, handle_voice))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
