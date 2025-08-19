import os
import telebot
from flask import Flask, request

# Инициализация бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Простейшие обработчики сообщений
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я работающий бот! ✅")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Вы написали: {message.text}")

# Для локальной разработки с polling
if __name__ == '__main__':
    print("Бот запущен в режиме polling...")
    bot.remove_webhook()
    bot.polling()