import logging
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import config
import random
import girls
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook


#WEBHOOK
API_TOKEN = config.TOKEN
WEBHOOK_HOST = 'https://love1s.bots.com'
WEBHOOK_PATH = '/path/to/api'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


# webserver settings
WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 3001

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

class Form(StatesGroup):
    name = State()
    age = State()
    text = State()

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await Form.name.set()
    # meeting user, add DB name ID
    await message.reply("Hi there! What's your name?")

@dp.message_handler(state='*', commands='help')
async def cmd_start(message: types.Message):
    await  message.reply("Did you get confused?\nTry again /start")

@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):

    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    await state.finish()

    await message.reply('Cancelled.')


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.reply("How old are you?")

@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):

    return await message.reply("Age gotta be a number.\nHow old are you? (digits only)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    # update state and data
    await Form.next()
    await state.update_data(age=int(message.text))
    await message.reply("What city are you from?")

@dp.message_handler(state=Form.city)
async def process_city(message: types.Message, state: FSMContext):
    # present meeting user
    async with state.proxy() as data:
        data['city'] = message.text
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Hi! Nice to meet you,', md.bold(data['name'])),
                md.text('Age:', md.code(data['age'])),
                md.text('City:', md.bold(data['city'])),
                sep='\n',
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb.for_state
        )
        await Form.next()

@dp.message_handler(lambda message: types.Message, state=Form.text)
async def process_photo_girs(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
        # ^_^ redirecting the user to the dating site
        if message.text == "For sex":
            await bot.send_photo(message.from_user.id, random.choice(girls.Photo_Sex),
                                 reply_to_message_id=message.message_id,
                                 caption=random.choice(girls.Name_Age),
                                 reply_markup=kb.inline_kb_full,
                                 parse_mode=ParseMode.MARKDOWN,
                                 )

        if message.text == "For relationship":
            await bot.send_photo(message.from_user.id, random.choice(girls.Photo),
                                 reply_to_message_id=message.message_id,
                                 caption=random.choice(girls.Name_Age),
                                 reply_markup=kb.inline_kb_full,
                                 parse_mode=ParseMode.MARKDOWN,
                                 )


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )