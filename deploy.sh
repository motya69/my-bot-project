#!/bin/bash

# Скрипт для деплоя бота на разные платформы
echo "Деплой Telegram-бота"

# Обновляем зависимости
pip install -r requirements.txt

# Копируем токен бота в переменные окружения (для разных платформ)
if [ "$1" = "render" ]; then
    echo "Деплой на Render..."
    # Render автоматически подхватит код из GitHub
elif [ "$1" = "railway" ]; then
    echo "Деплой на Railway..."
    # Railway автоматически подхватит код из GitHub
elif [ "$1" = "flyio" ]; then
    echo "Деплой на Fly.io..."
    flyctl deploy
else
    echo "Укажите платформу: render, railway или flyio"
fi