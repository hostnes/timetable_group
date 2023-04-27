import datetime
import json
import logging
import time

import requests
from aiogram import Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton
from selenium import webdriver

from tier_state import InstallGroupState
from connect_server import users_service
from bot_creation import bot


import os
logging.basicConfig(level=logging.INFO)

dp = Dispatcher(bot, storage=MemoryStorage())

group = ['160*', '161*', '162*', '163*', '164*', '41', '42',
         '43', '44', '45', '46', '48', '49', '50', '51',
         '52', '53', '54', '55', '56', '57', '58', '59*',
         '60', '61', '62', '63', '64', '65', '66', '67',
         '68', '69', '7', '70', '71', '72', '73', '74',
         '75', '76', '77', '78', '8']

week_days = {
    0: 'понедельник',
    1: 'вторник',
    2: 'среда',
    3: 'четверг',
    4: 'пятница',
    5: 'суббота',
    6: 'понедельник',
}


async def startup(_):
    users_service.check_connect()


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    query_params = {'telegram_id': message.from_user.id}
    user_response = users_service.get_users(query_params)
    reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if len(user_response) == 0:
        reply_kb.add(KeyboardButton("🍻 Установить группу 🍻"))
    else:
        pagination_buttons = []
        pagination_buttons_2 = []
        pagination_buttons.append(KeyboardButton("🪦Расписание на день🪦"))
        pagination_buttons.append(KeyboardButton("♿️Расписание на неделю♿"))
        reply_kb.row(*pagination_buttons)
        pagination_buttons_2.append(KeyboardButton("👞🔄👟 Изменить группу"))
        pagination_buttons_2.append(KeyboardButton("🗿Расписание звонков🗿"))
        reply_kb.row(*pagination_buttons_2)
        if user_response[0]['is_sender'] == True:
            reply_kb.add(KeyboardButton("🔕 Отписаться от рассылки"))
        else:
            reply_kb.add(KeyboardButton("🔔 Подписаться на расслыку"))
    if len(user_response) != 1:
        user_data = {'first_name': message.from_user.first_name,
                     'telegram_id': message.from_user.id}
        response = users_service.post_user(user_data)
    await message.answer('Тыкай', reply_markup=reply_kb)


@dp.message_handler(text='🪦Расписание на день🪦')
async def day_lessons(message: types.Message):
    query_params = {'telegram_id': message.from_user.id}
    response = users_service.get_users(query_params)
    group_number = str(response[0]['group_number'])
    if int(datetime.datetime.now().hour) >= 14:
        week_day_today = week_days[1 + int(datetime.datetime.weekday(datetime.datetime.today()))]
    else:
        week_day_today = week_days[datetime.datetime.weekday(datetime.datetime.today())]
    with open('server/bot/data/lessons.json') as file:
        src = json.load(file)
    for item in src:
        for key, value in item.items():
            if key == group_number:
                jsona = item
    text = ''
    if datetime.datetime.weekday(datetime.datetime.today()) == 5:
        text += f'*Группа {group_number} - {week_day_today}*\n'
        text += f'\nпар нет иди раскумарься'
        week_day_today = week_days[0]
        await message.answer(text, parse_mode="Markdown")
    text = ''
    text += f'*Группа {group_number} - {week_day_today}*\n'
    if len(src) <= 20:
        text += '\n\nпар нет, иди раскумарься'
    elif jsona[group_number]['number_lessons'] != None:
        count = 0
        try:
            if int(jsona[group_number]['number_lessons'][0]) != 1:
                text += '\n*1 пара*\n-\nкаб: -\n'
                if int(jsona[group_number]['number_lessons'][0]) != 2:
                    text += '\n*2 пара*\n-\nкаб: -\n'
            for i in range(int(jsona[group_number]['number_lessons'][0]), int(jsona[group_number]['number_lessons'][-1]) + 1):
                text += f'\n*{jsona[group_number]["number_lessons"][count]} пара*\n'
                if '3' in jsona[group_number]["lessons"][count]:
                    lessons = jsona[group_number]["lessons"][count].split('2')
                    text += f'{lessons[0]} \n'
                    lessons_2 = lessons[-1].split('3')
                    text += f'2{lessons_2[0]} \n'
                    text += f'3{lessons_2[1]} \n'

                elif '2' in jsona[group_number]["lessons"][count]:
                    lessons = jsona[group_number]["lessons"][count].split('2')
                    text += f'{lessons[0]} \n'
                    text += f'2{lessons[-1]} \n'
                else:
                    text += f'{jsona[group_number]["lessons"][count]} \n'

                cabinets = ''
                for a in jsona[group_number]["cabinets"][count]:
                    cabinets += a
                    cabinets += ' '
                text += f'каб: {cabinets} \n'
                count += 1
        except:
            pass
    else:
        text += '\nпар нет, иди расчилься'

    await message.answer(text, parse_mode="Markdown")


@dp.message_handler(text='♿️Расписание на неделю♿')
async def week_lessons(message: types.Message):
    query_params = {'telegram_id': message.from_user.id}
    response = users_service.get_users(query_params)
    group_number = str(response[0]['group_number'])
    await bot.send_photo(chat_id=message.chat.id, photo=open(f'server/bot/data/{group_number}.png', 'rb'))


@dp.message_handler(text='👞🔄👟 Изменить группу')
async def change_group(message: types.Message, state: FSMContext):
    query_params = {'telegram_id': message.from_user.id}
    response = users_service.get_users(query_params)
    await state.update_data(user_id=response[0]['id'])
    await state.update_data(is_sender=response[0]['is_sender'])

    await message.answer('введите номер группы: ', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(InstallGroupState.get_group.state)


@dp.message_handler(text='🍻 Установить группу 🍻')
async def install_group(message: types.Message, state: FSMContext):
    query_params = {'telegram_id': message.from_user.id}
    response = users_service.get_users(query_params)
    await state.update_data(user_id=response[0]['id'])
    await message.answer('введите номер группы: ', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(InstallGroupState.get_group.state)


@dp.message_handler(state=InstallGroupState.get_group.state)
async def get_group_for_install(message: types.Message, state: FSMContext):
    data = await state.get_data()
    reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    pagination_buttons = []
    pagination_buttons_2 = []
    pagination_buttons.append(KeyboardButton("🪦Расписание на день🪦"))
    pagination_buttons.append(KeyboardButton("♿️Расписание на неделю♿"))
    reply_kb.row(*pagination_buttons)
    pagination_buttons_2.append(KeyboardButton("👞🔄👟 Изменить группу"))
    pagination_buttons_2.append(KeyboardButton("🗿Расписание звонков🗿"))
    reply_kb.row(*pagination_buttons_2)
    if data['is_sender'] == True:
        reply_kb.add(KeyboardButton("🔕 Отписаться от рассылки"))
    else:
        reply_kb.add(KeyboardButton("🔔 Подписаться на расслыку"))
    if message.text in group:
        user_data = {'group_number': message.text}
        response = users_service.patch_user(user_id=data['user_id'], user_data=user_data)
        await message.answer('окэ', reply_markup=reply_kb)
        await state.finish()
    else:
        await message.answer('введи норм группу э:')


@dp.message_handler(text='🔔 Подписаться на расслыку')
async def is_sender(message: types.Message):
    pagination_buttons = []
    pagination_buttons_2 = []
    query_params = {'telegram_id': message.from_user.id}
    response = users_service.get_users(query_params)
    user_id = response[0]['id']
    reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    pagination_buttons.append(KeyboardButton("🪦Расписание на день🪦"))
    pagination_buttons.append(KeyboardButton("♿️Расписание на неделю♿"))
    reply_kb.row(*pagination_buttons)
    pagination_buttons_2.append(KeyboardButton("👞🔄👟 Изменить группу"))
    pagination_buttons_2.append(KeyboardButton("🗿Расписание звонков🗿"))
    reply_kb.row(*pagination_buttons_2)
    user_data = {'is_sender': True}
    response = users_service.patch_user(user_id=user_id, user_data=user_data)
    reply_kb.add(KeyboardButton("🔕 Отписаться от рассылки"))
    await message.answer('Тыкай', reply_markup=reply_kb)


@dp.message_handler(text='🔕 Отписаться от рассылки')
async def is_sender(message: types.Message):
    pagination_buttons = []
    pagination_buttons_2 = []
    query_params = {'telegram_id': message.from_user.id}
    response = users_service.get_users(query_params)
    user_id = response[0]['id']
    reply_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    pagination_buttons.append(KeyboardButton("🪦Расписание на день🪦"))
    pagination_buttons.append(KeyboardButton("♿️Расписание на неделю♿"))
    reply_kb.row(*pagination_buttons)
    pagination_buttons_2.append(KeyboardButton("👞🔄👟 Изменить группу"))
    pagination_buttons_2.append(KeyboardButton("🗿Расписание звонков🗿"))
    reply_kb.row(*pagination_buttons_2)
    user_data = {'is_sender': False}
    reply_kb.add(KeyboardButton("🔔 Подписаться на расслыку"))
    response = users_service.patch_user(user_data, user_id)
    await message.answer('Тыкай', reply_markup=reply_kb)

@dp.message_handler(text='🗿Расписание звонков🗿')
async def install_group(message: types.Message, state: FSMContext):
    await message.answer('🤹 ‍️БУДНИ 🤹️\n1. 09:00 - 09:45 | 09:55 - 10:40\n2. 10:50 - 11:35 | 11:55 - 12:40\n3. 13:00 - 13:45 | 13:55 - 14:40\n4. 14:50 - 15:35 | 15:45 - 16:30\n'
                         '\n🏳️‍🌈 СУББОТА 🏳️‍🌈\n1. 09:00 - 09:45 | 09:55 - 10:40\n2. 10:50 - 11:35 | 11:50 - 12:35\n3. 12:50 - 13:35 | 13:45 - 14:30\n4. 14:40 - 15:25 | 15:35 - 16:20\n')

@dp.message_handler(commands=["info"])
async def info(msg: types.Message):
    await msg.answer("Самый лучший бот, для самого лучшего коллджа МИРА 😈😈😈\n"
                     "Создатель: @hostnes")


executor.start_polling(dp, skip_updates=True, on_startup=startup)