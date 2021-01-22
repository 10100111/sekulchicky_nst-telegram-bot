import logging
import io
from PIL import Image
from os import path, environ
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils import get_number_of_styles
from model import StyleModel

dotenv_path = path.join(path.dirname(__file__), '.env')
# Take environment variables from .env.
load_dotenv(dotenv_path)

API_TOKEN = environ.get("TELEGRAM_API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Bot states
class BotStates(StatesGroup):
    waiting_select_style = State()
    waiting_photo = State()
    waiting_processing = State()


# Styles
n_styles, user_style = 0, 0


@dp.message_handler(state='*', commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    global user_style
    global n_styles
    user_style = 0
    n_styles = get_number_of_styles()
    await BotStates.waiting_select_style.set()
    await message.reply("Привет!!!\nЯ neural-style-transfer бот.\n"
                        "Я могу накладывать различные стили на фотографии.\n"
                        "Для выбора стиля нажми /style, затем задай номер стиля и загрузи фотку.\n")


@dp.message_handler(state=BotStates.waiting_select_style, commands=['style'])
async def handle_style(message):
    global user_style
    if user_style == 0:
        await message.reply(f"Для выбора стиля, набери число от 1 до {n_styles}.\n")
    else:
        await message.reply(f"Осталось загрузить какую-нибудь фотографию.\n")
        await BotStates.waiting_photo.set()


@dp.message_handler(state=BotStates.waiting_select_style)
async def style_select(message: types.Message):
    global user_style
    try:
        user_style = int(message.text.strip())
    except ValueError:
        await message.reply("Некорректный ввод данных\n")
        return
    if 0 < user_style <= n_styles:
        await message.answer(f"Поздравляю! Ты выбрал стиль под номером {user_style}.\n"
                             f"Осталось загрузить какую-нибудь фотографию.\n")
        await BotStates.waiting_photo.set()
    else:
        await message.reply("Некорректный ввод данных\n")
        await message.answer("Стиля с таким номером не существует.\n"
                             f"Попробуй ввести от 1 до {n_styles}.\n")


@dp.message_handler(state=BotStates.waiting_photo, content_types=['photo'])
async def handle_photo(message: types.Message):
    """
    This handler will be saved user's photo
    """
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    image_data = await bot.download_file(file_info.file_path)
    content_image = Image.open(image_data)
    await BotStates.waiting_processing.set()
    await handle_go_processing(message, content_image)


@dp.message_handler(state=BotStates.waiting_processing)
async def handle_go_processing(message, content_image):
    global user_style
    await message.answer("Я приступил к обработке фотографии. Это может занять какое-то время..\n"
                         "...\n")
    output_image = await stylize(content_image)
    user_style = 0
    await bot.send_photo(chat_id=message.from_user.id, photo=output_image)
    await message.answer("Посмотри как получилось! Если хочешь еще, жми /style.\n")
    await BotStates.waiting_select_style.set()


async def stylize(content_image):
    global user_style
    model = StyleModel(user_style)
    model.load_model()
    output = model.run(content_image)
    return output

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)