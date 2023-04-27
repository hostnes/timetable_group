import asyncio
import datetime
import os

import requests
from celery.task import periodic_task
from celery.schedules import crontab

import time
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bot.bot_creation import bot
week_days = {
    0: 'понедельник',
    1: 'вторник',
    2: 'среда',
    3: 'четверг',
    4: 'пятница',
    5: 'суббота',
    6: 'понедельник',
}
bad_group_numbers = {
    '160*': '160',
    '161*': '161',
    '162*': '162',
    '163*': '163',
    '164*': '164',

}

group = ['160*', '161*', '162*', '163*', '164*', '41', '42',
         '43', '44', '45', '46', '48', '49', '50', '51',
         '52', '53', '54', '55', '56', '57', '58', '59*',
         '60', '61', '62', '63', '64', '65', '66', '67',
         '68', '69', '7', '70', '71', '72', '73', '74',
         '75', '76', '77', '78', '8']


# @periodic_task(run_every=(crontab(hour=14, minute=20)), name='driver_task')
@periodic_task(run_every=(crontab(hour=14, minute=20)), name='driver_task')
def driver_task():
    driver = webdriver.Remote('http://selenium:4444', desired_capabilities=DesiredCapabilities.CHROME)
    try:
        driver.get(url='https://mgkct.minskedu.gov.by/персоналии/учащимся/расписание-занятий-на-день')
        time.sleep(3)
        with open('bot/data/day.html', 'w') as file:
            file.write(driver.page_source)
    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        pars_html()


@periodic_task(run_every=(crontab(hour=15, day_of_week='Saturday')), name='week_task')
def week_task():
    driver = webdriver.Remote('http://selenium:4444', desired_capabilities=DesiredCapabilities.CHROME)
    for i in group:
        driver.get(url=f'https://mgkct.minskedu.gov.by/персоналии/учащимся/расписание-занятий-на-неделю?group={i}')
        with open('service/templates/week.html', 'w') as file:
            file.write(driver.page_source)
        driver.get(url=f'http://web-app:8000/api/week/')
        driver.set_window_size(1870, 820)
        driver.execute_script("window.scrollTo(0, 2320)")
        driver.save_screenshot(f'bot/data/{i}.png')
    driver.close()


def pars_html():
    week_day_today = week_days[1 + datetime.datetime.weekday(datetime.datetime.today())]
    with open('bot/data/day.html') as file:
        src = file.read()
    data = []
    soup = BeautifulSoup(src, 'lxml')
    group_lxml = soup.find('div', id="wrapperTables").find_all('div')
    group = []

    for item in group_lxml[::2]:
        group.append(item.text.strip().split(' ')[0])
    for group_number in group:
        if group_number == 'Лицей':
            break
        number_lessons = []
        lessons = []
        cabinets = []
        bad_group = ['160*', '161*', '162*', '163*', '164*']
        driver = soup.find('div', string=f'{group_number} - {week_day_today}').find_next().find_all('tr')

        if len(driver) != 0:
            for i in driver[0].find_all('th'):
                number_lessons.append(i.text.strip().split('№')[-1])

            for i in driver[1].find_all('td'):
                lessons.append(i.text.strip())

            for i in driver[2].find_all('td'):
                test = []
                for item in i:
                    if str(item) == '<br/>':
                        pass
                    else:
                        test.append(item)
                cabinets.append(test)
            correctness_data = len(lessons) - len(cabinets)
            for i in range(0, correctness_data):
                cabinets.append(['-'])

            if group_number in bad_group:
                group_number = bad_group_numbers[group_number]
            data.append({f'{group_number}': {
                'number_lessons': number_lessons,
                'lessons': lessons,
                'cabinets': cabinets,
                }
            })
        else:
            if group_number in bad_group:
                group_number = bad_group_numbers[group_number]
            data.append({f'{group_number}': {
                'number_lessons': None,
                'lessons': None,
                'cabinets': None,
                }
            })

        with open('bot/data/lessons.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    asyncio.run(class_schedule())


async def class_schedule():
    users = requests.get(f"http://{os.environ['WEB_APP_HOST']}:8000/api/users/")
    for user in users.json():
        if user['is_sender'] == True:
            group_number = str(user['group_number'])
            if int(datetime.datetime.now().hour) >= 14:
                week_day_today = week_days[1 + int(datetime.datetime.weekday(datetime.datetime.today()))]
            else:
                week_day_today = week_days[datetime.datetime.weekday(datetime.datetime.today())]
            with open('bot/data/lessons.json') as file:
                src = json.load(file)
            for item in src:
                for key, value in item.items():
                    if key == group_number:
                        jsona = item
            text = ''
            if datetime.datetime.weekday(datetime.datetime.today()) == 5:
                text += f'*Группа {group_number} - воскресенье*\n'
                text += f'\nпар нет иди раскумарься'
                week_day_today = 'понедельник'
                await bot.send_message(chat_id=str(user['telegram_id']), text=text, parse_mode="Markdown")
            text = ''
            text += f'*Группа {group_number} - {week_day_today}*\n'
            try:
                if len(src) <= 20:
                    text += '\n\nпар нет, иди раскумарься'
                elif jsona[group_number]['number_lessons'] != None:
                    count = 0
                    if int(jsona[group_number]['number_lessons'][0]) != 1:
                        text += '\n*1 пара*\n-\nкаб: -\n'
                        if int(jsona[group_number]['number_lessons'][0]) != 2:
                            text += '\n*2 пара*\n-\nкаб: -\n'
                    for i in range(int(jsona[group_number]['number_lessons'][0]),
                                   int(jsona[group_number]['number_lessons'][-1]) + 1):
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
                else:
                    text += '\nпар нет, иди расчилься'
            except:
                pass
            await bot.send_message(chat_id=str(user['telegram_id']), text=text, parse_mode="Markdown")