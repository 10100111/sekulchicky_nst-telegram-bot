import logging
from os import path, environ
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types


dotenv_path = path.join(path.dirname(__file__), '.env')
# Take environment variables from .env.
load_dotenv(dotenv_path)

API_TOKEN = environ.get("TELEGRAM_API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Привет!\nЯ neural-style-transfer бот.\n"
                        "Я могу перенести стиль с картины великого художнико, например Ван Гога"
                        " на твою фотографию.\n"
                        "Для выбора стиля нажми /style, затем задай номер стиля.\n"
                        "Доступные стили:\n"
                        "Pollock - 1\n"
                        "Van Gogh - 2\n")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)