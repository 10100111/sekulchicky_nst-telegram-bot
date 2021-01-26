import logging
import io
from PIL import Image
from os import path, environ
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import emoji
from utils import get_number_of_styles, get_examples
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


def set_keyboard():
    btn1 = types.InlineKeyboardButton(text="\U0001F3A8 Стилизовать", callback_data='style')
    btn2 = types.InlineKeyboardButton(text="\U0001F5BC Показать примеры", callback_data='example')
    btn3 = types.InlineKeyboardButton(text="\U0001F4BB Репозиторий проекта",
                                      url='https://github.com/sekulchicky/nst-telegram-bot')
    keyboard_markup = types.InlineKeyboardMarkup().add(btn1).add(btn2).add(btn3)
    return keyboard_markup


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
    await message.reply(f"Привет, *{message.from_user.username}*!\n", parse_mode='Markdown')
    await message.answer("Я *Neural-Style-Transfer* бот \U0001F916\n\n"
                         f"*Что я умею ?*\n"
                         f"Я могу стилизовать твою фотографию при помощи искусственной нейросети. На данный момент"
                         f" в моем арсенале имеется {n_styles} различных стилей \U0001F3A8\n\n"
                         f"Также, ты можешь посмотреть примеры уже стилизованных фотографий или посетить"
                         f" репозиторий данного проекта \U0001F609\n\n"
                         f"*Как управлять ?*\n"
                         f"Управление происходит через встроенную клавиатуру"
                         f"\U0001F447\U0001F447\U0001F447\nНо незабывай, ты всегда можешь вызвать /help для помощи."
                         f"\n\nEnjoy it! \U0001F60F",
                         reply_markup=set_keyboard(), parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data == 'style', state=BotStates.waiting_select_style)
async def process_callback_btn1(query: types.CallbackQuery):
    global user_style
    await bot.answer_callback_query(query.id, f"\U0001F3A8")
    if user_style == 0:
        await bot.send_message(query.from_user.id,
                               text=f"Для выбора стиля, набери число от *1* до *{n_styles}*", parse_mode='Markdown')
    else:
        await bot.send_message(query.from_user.id, text="Осталось загрузить какую-нибудь фотографию")
        await BotStates.waiting_photo.set()


@dp.callback_query_handler(lambda c: c.data == 'example', state='*')
async def process_callback_btn2(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id, f"\U0001F5BC")
    await bot.send_message(query.from_user.id, f"Загружаю для тебя примеры...")
    media = types.MediaGroup()
    for img, name in get_examples():
        media.attach_photo(types.InputFile(img), name)
    await bot.send_media_group(query.from_user.id, media=media)
    await bot.send_message(query.from_user.id, "Порядковый номер изображения соответствует номеру стиля.",
                           reply_markup=set_keyboard())


@dp.message_handler(state=BotStates.waiting_select_style)
async def style_select(message: types.Message):
    global user_style
    try:
        user_style = int(message.text.strip())
    except ValueError:
        await message.reply("\U0000274EНекорректный ввод данных\n")
        return
    if 0 < user_style <= n_styles:
        await message.answer(f"\U00002705Ты выбрал стиль под номером *{user_style}*.\n"
                             f"Осталось загрузить какую-нибудь фотографию.\n", parse_mode='Markdown')
        await BotStates.waiting_photo.set()
    else:
        await message.reply("\U0000274EНекорректный ввод данных\n")
        await message.answer("К сожалению стиля с таким номером не существует.\n"
                             f"Попробуй ввести от *1* до *{n_styles}* \U0001F9D0\n", parse_mode='Markdown')


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
    await message.answer("Я приступил к обработке фотографии.\n"
                         f"Это может занять какое-то время.\n")
    await message.answer("\U000023F3...\n")
    output_image = await stylize(content_image)
    user_style = 0
    await bot.send_photo(chat_id=message.from_user.id, photo=output_image)
    await message.answer("Готово! \U0001F64C\n\nЕсли хочешь попробовать еще, жми\U0001F447\U0001F447",
                         reply_markup=set_keyboard())
    await BotStates.waiting_select_style.set()


async def stylize(content_image):
    global user_style
    model = StyleModel(user_style)
    model.load_model()
    output = model.run(content_image)
    return output


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
