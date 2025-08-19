import os
import telebot
from flask import Flask, request
from dotenv import load_dotenv  # Добавляем импорт

# Загружаем переменные из .env файла (для локальной разработки)
load_dotenv()

# Проверяем, что токен установлен
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Убедитесь, что он установлен в переменных окружения или в файле .env")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Простейшие обработчики сообщений
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Ух, кажись я запустился. Напиши мне что-нибудь✅")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Повторюшка: {message.text}")

# Для локальной разработки с polling
if __name__ == '__main__':
    print("Бот запущен в режиме polling...")
    bot.remove_webhook()
    bot.polling()