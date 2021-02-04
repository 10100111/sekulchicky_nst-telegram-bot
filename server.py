import logging
from _io import BytesIO
from os import path, environ
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.executor import start_webhook
from utils import get_list_of_styles, get_examples
from model import StyleModel
import gc

if path.exists(path.dirname(__file__)):
    # Take environment variables from .env.
    # Use if LOCAL DEBUG
    dotenv_path = path.join(path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)

API_TOKEN = environ.get("TELEGRAM_API_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

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
n_styles, style_names, user_style = 0, list(), 0
content_img = BytesIO()


def set_keyboard(condition=True):
    """
    Инициализация инлайн-клавиатуры
    """
    btn1 = types.InlineKeyboardButton(text="🎨 Стилизовать", callback_data='style')
    btn2 = types.InlineKeyboardButton(text="🖼️ Показать примеры", callback_data='example')
    btn3 = types.InlineKeyboardButton(text="📷 Загрузить фотографию", callback_data='photo')
    btn4 = types.InlineKeyboardButton(text="🖥️ Репозиторий проекта",
                                      url='https://github.com/sekulchicky/nst-telegram-bot')
    if condition is False:
        keyboard_markup = types.InlineKeyboardMarkup().add(btn1).add(btn3)
    else:
        keyboard_markup = types.InlineKeyboardMarkup().add(btn3).add(btn2).add(btn4)

    return keyboard_markup


async def stylize(content_image):
    """
    Вызов модели для стилизации контент-изображения
    """
    global user_style
    model = StyleModel(user_style)
    model.load_model()
    output = model.run(content_image)
    del model
    gc.collect()
    return output


@dp.message_handler(state='*', commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    Обработчик комманд `/start` or `/help`
    """
    global user_style, style_names, n_styles
    user_style = 0
    style_names = get_list_of_styles()
    n_styles = len(style_names)
    await BotStates.waiting_select_style.set()
    await message.reply(f"Привет, *{message.from_user.username}*!\n", parse_mode='Markdown')
    await message.answer("Я *Neural-Style-Transfer* бот 🤖\n\n"
                         f"*Что я умею ?*\n"
                         f"Я могу стилизовать твою фотографию при помощи искусственной нейросети. На данный момент"
                         f" в моем арсенале имеется {n_styles} различных стилей 🎨\n\n"
                         f"Также, ты можешь посмотреть примеры уже стилизованных фотографий или посетить"
                         f" репозиторий данного проекта 😉\n\n"
                         f"*Как управлять ?*\n"
                         f"Управление происходит через встроенную клавиатуру"
                         f"👇👇👇\nНо не забывай, ты всегда можешь вызвать /help для помощи."
                         f"\n\nEnjoy it!😏",
                         reply_markup=set_keyboard(), parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data == 'style', state=BotStates.waiting_select_style)
async def process_callback_btn1(query: types.CallbackQuery):
    """
    Обработчик кнопки 'Стилизовать'
    """
    global user_style, style_names
    await bot.answer_callback_query(query.id, f"🎨")
    if user_style == 0:
        style_text = ''
        for i, s_name in enumerate(style_names):
            style_text += f"{i + 1}) -  {s_name};\n\n"
        await bot.send_message(query.from_user.id,
                               text=f"Доступные стили:\n\n"
                                    f"{style_text}\n"
                                    f"Чтобы выбрать стиль, просто введи его номер.")
    else:
        await bot.send_message(query.from_user.id, text="Осталось загрузить какую-нибудь фотографию")
        await BotStates.waiting_photo.set()


@dp.callback_query_handler(lambda c: c.data == 'example', state='*')
async def process_callback_btn2(query: types.CallbackQuery):
    """
    Обработчик кнопки 'Показать примеры'
    """
    await bot.answer_callback_query(query.id, f"🖼️")
    await bot.send_message(query.from_user.id, f"Загружаю для тебя примеры...")
    media = types.MediaGroup()
    for img, name in get_examples():
        media.attach_photo(types.InputFile(img), name)
    await bot.send_media_group(query.from_user.id, media=media)
    await bot.send_message(query.from_user.id, "Порядковый номер изображения соответствует номеру стиля.",
                           reply_markup=set_keyboard())


@dp.callback_query_handler(lambda c: c.data == 'photo', state='*')
async def process_callback_btn3(query: types.CallbackQuery):
    """
    Обработчик кнопки 'Загрузить фотографию'
    """
    await bot.answer_callback_query(query.id, f"📷")
    await bot.send_message(query.from_user.id, f"Загрузи фотографию, которую хочешь стилизовать. Если ты используешь"
                                               f"декстопную версию Telegram, то не забудь поставить галочку "
                                               f"☑ `Compress images`", parse_mode='Markdown')
    await BotStates.waiting_photo.set()


@dp.message_handler(state=BotStates.waiting_select_style)
async def style_select(message: types.Message):
    """
    Обработчик выбора стиля, вызывается при указании номера стиля
    """
    global user_style, style_names, n_styles, content_img
    try:
        user_style = int(message.text.strip())
    except ValueError:
        await message.reply("❎ Некорректный ввод данных\n")
        return
    if 0 < user_style <= n_styles:
        await message.answer(f"✅ Ты выбрал стиль _{style_names[user_style - 1]}_.\n", parse_mode='Markdown')
        await BotStates.waiting_processing.set()
        await handle_go_processing(message)
    else:
        await message.reply("❎ Некорректный ввод данных\n")
        await message.answer("К сожалению стиля с таким номером не существует.\n"
                             f"Попробуй ввести от *1* до *{n_styles}* 🧐\n", parse_mode='Markdown')


@dp.message_handler(state=BotStates.waiting_photo, content_types=['photo'])
async def handle_photo(message: types.Message):
    """
    Вызывается при отправке пользователем фотографии
    """
    global content_img, user_style
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    content_img = await bot.download_file(file_info.file_path)
    # content_img = Image.open(image_data)
    # print(type(image_data))
    await BotStates.waiting_select_style.set()
    await message.answer("Фотография успешно загружена.\n", reply_markup=set_keyboard(False))


@dp.message_handler(state=BotStates.waiting_processing)
async def handle_go_processing(message):
    """
    Стилизация
    """
    global user_style, content_img
    await message.answer("Я приступил к обработке фотографии.\n"
                         f"Это может занять какое-то время.\n")
    await message.answer("\U000023F3...\n")
    output_image = await stylize(content_img)
    user_style = 0
    await bot.send_photo(chat_id=message.from_user.id, photo=output_image)
    await message.answer("Готово!👍👍\n\nЕсли хочешь попробовать еще, жми👇👇",
                         reply_markup=set_keyboard(False))
    await BotStates.waiting_select_style.set()


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Start webhook..\tWEBAPP_HOST-{WEBAPP_HOST}; WEBAPP_PORT-{WEBAPP_PORT};\n"
                 f"WEBAPP_URL-{WEBHOOK_URL};")


async def on_shutdown(dp):
    logging.warning("Shutting down..")
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bye!")


if __name__ == '__main__':

    webhook_settings = False if environ.get('LOCAL_DEBUG') else True

    if webhook_settings:
        WEBHOOK_HOST = environ.get("WEBHOOK_HOST_ADDR")
        WEBHOOK_PATH = f"webhook/{API_TOKEN}/"
        WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
        WEBAPP_HOST = environ.get("WEBAPP_HOST")
        WEBAPP_PORT = environ.get("PORT")

        start_webhook(
            dispatcher=dp,
            webhook_path=f"/{WEBHOOK_PATH}",
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=False,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
    else:
        executor.start_polling(dp, skip_updates=True)
