import logging
from os import path, environ
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from utils import get_number_of_styles

dotenv_path = path.join(path.dirname(__file__), '.env')
# Take environment variables from .env.
load_dotenv(dotenv_path)

API_TOKEN = environ.get("TELEGRAM_API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Styles
n_styles = get_number_of_styles()
user_style = 0


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """

    await message.reply("Привет!\nЯ neural-style-transfer бот.\n"
                        "Я могу перенести стиль с картины великого художника, например Ван Гога"
                        "на твою фотографию.\n"
                        "Для выбора стиля нажми /style, затем задай номер стиля.\n")


@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    """
    This handler will be saved user's photo
    """
    await message.photo[-1].download(f'/images/{message.from_user.id}_content.jpg')


@dp.message_handler(commands=['style'])
async def handle_style(message):
    global user_style
    if user_style == 0:
        await message.reply(f"Для выбора стиля, набери число от 1 до {n_styles}.\n")
    else:
        await message.reply(f"Осталось загрузить какую-нибудь фотографию.\n")


@dp.message_handler()
async def style_select(message: types.Message):
    global user_style
    try:
        user_style = int(message.text.strip())
    except ValueError:
        await message.reply("Некорректный ввод данных\n")
        return
    if user_style > n_styles:
        await message.reply("Некорректный ввод данных\n")
        await message.answer("Стиля с таким номером не существует.\n"
                             f"Попробуй ввести от 1 до {n_styles}.\n")
    else:
        await message.answer(f"Поздравляю! Ты выбрал стиль под номером {user_style}.\n")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)