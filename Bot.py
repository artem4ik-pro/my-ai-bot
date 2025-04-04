from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
import asyncio
from aiogram.enums.parse_mode import ParseMode
from mistralai import Mistral
from aiogram.exceptions import TelegramAPIError
from dotenv import load_dotenv
import os

# Загрузка переменных из .env
load_dotenv()

# Инициализация бота с использованием переменных окружения
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
api_key = os.getenv('MISTRAL_API_KEY')
model = os.getenv('MISTRAL_MODEL')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = Mistral(api_key=api_key)

# Глобальный словарь для хранения истории диалогов
chat_history = {}

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    chat_id = message.chat.id
    chat_history[chat_id] = []  # Инициализация истории для нового пользователя
    await message.reply("Привет! Я бот, который общается с помощью AI. Напиши мне что-нибудь!")


# Команда /help
@dp.message(Command("help"))
async def send_help(message: Message):
    await message.reply("Просто напиши мне сообщение, и я отвечу с помощью AI.")


# Обработка текстовых сообщений
@dp.message()
async def echo(message: types.Message):
    chat_id = message.chat.id
    user_message = message.text
# Пасхалка: если пользователь написал "мтуси" (регистронезависимо)
    if "мтуси" in user_message.lower():
        # Отправляем картинку
        photo = FSInputFile('egg.png')
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption="МТУСИ — лучший университет! 🎓")
        return  # Завершаем обработку, чтобы не продолжать диалог
    await message.answer_sticker("CAACAgEAAxkBAAEOEcFn76OxGbvnZBSI1bdTVY-OaivYYgACcgIAAnBGIUaaOxHkwIfGujYE")
    # Добавляем сообщение пользователя в историю
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append({"role": "user", "content": user_message})

    # Ограничение длины истории (например, до 10 сообщений)
    if len(chat_history[chat_id]) > 10:  # Ограничение истории до 10 сообщений
        chat_history[chat_id] = chat_history[chat_id][-10:]  # Оставляем последние 10 сообщений

    # Отправляем временное сообщение
    try:
        temp_message = await message.reply("Принял😉 Обрабатываю!")
    except TelegramAPIError as e:
        print(f"Ошибка при отправке временного сообщения: {e}")
        return

    # Получаем ответ от Mistral API
    try:
        response = await get_ai_response(chat_history[chat_id])
        chat_history[chat_id].append({"role": "assistant", "content": response})  # Добавляем ответ в историю
    except Exception as e:
        # Если произошла ошибка при запросе к API
        await message.reply(f"Произошла ошибка при обработке запроса: {e}")
        return
    finally:
        # Удаляем временное сообщение
        try:
            await bot.delete_message(chat_id=chat_id, message_id=temp_message.message_id)
        except TelegramAPIError as e:
            print(f"Ошибка при удалении временного сообщения: {e}")

    # Отправляем ответ пользователю
    await message.reply(response, parse_mode=ParseMode.MARKDOWN)


# Запрос к Mistral API
async def get_ai_response(messages):
    try:
        chat_response = client.chat.complete(
            model=model,
            messages=messages
        )
        return chat_response.choices[0].message.content.replace('**', '*').replace('#', '')
    except Exception as e:
        raise Exception(f"Ошибка при запросе к Mistral API: {e}")


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
