import asyncio
import requests
import sqlite3
import json
from configparser import ConfigParser
from asyncio import sleep
from datetime import date, time
from threading import Thread
from sqlalchemy import create_engine, Table, Column, Integer, BigInteger, String, DateTime, MetaData


# conn = sqlite3.connect('example.db')
# c = conn.cursor()
# c.execute('''CREATE TABLE stocks
#              (date text, trans text, symbol text, qty real, price real)''')
# c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")
# conn.commit()
#
# t = ('RHAT',)
# c.execute('SELECT * FROM stocks WHERE symbol=?', t)
# print(c.fetchone())
#
# conn.close()

data = {
    'datetime': '2024-04-09 10:00',
    'tasks_no_employees': {
        '#180001': 'http://#',
        '#180002': 'http://#',
        '#180003': 'http://#',
        '#180004': 'http://#',
        '#180005': 'http://#',
        '#180006': 'http://#',
        '#180007': 'http://#'
    },
    'employees': {
        'Александр Костромичев': {
            'state': 'work/nowork/weekend',
            'working_days': 26,
            'weekend_days': 4,
            'assigned_applications': {
                'count': 2,
                'url': 'http://#'
            },
            'applications_in_execution': {
                'count': 1,
                'url': 'http://#',
                'task': [{
                    'task_state': True,
                    'task_id': 179990,
                    'task_url': 'http://#',
                    'task_deltatime': '0ч 23м',
                    'task_time': '2024-04-08 17:45',
                    'task_type': 'Заявки абонентов (РЕД)',
                    'task_subtype': '"Настроить роутер"',
                    'task_login_biling': 'sbnt2402030',
                    'task_login_oper': 'sbnt2402030',
                    'task_name_biling': 'Хаджимурад Рамазанкадиев Гамзатханович',
                    'task_name_oper': 'Хаджимурад Рамазанкадиев Гамзатханович',
                    'task_address_biling': 'Мах, Коркмасова - Советская, 106',
                    'task_address_oper': 'Коркмасова - Советская, д. 106',
                },]
            },
            'completed_today': {
                'count': 3,
                'url': 'http://#'},
            'completed_in_a_month': {
                'count': 45,
                'url': 'http://#'},
            'last_request': '2024-04-08 10:15'
        },
        'Али Исупов': {},
        'Анвер Магомедов': {},
        'Артур Мисриев': {},
        'Гамзат Гасанов': {},
        'Камиль Гаджиомаров': {},
    }
}

# Запись данных в JSON-файл
with open('data.json', 'w', encoding='utf-8') as f:
    # Вариант с красивым форматированием:
    json.dump(data, f, ensure_ascii=False, indent=4)
    # Вариант без форматирования:
    # json.dump(data, f, ensure_ascii=False)

with open('data.json', 'r', encoding='utf-8') as f:
    data_loaded = json.load(f)
    print(data_loaded)  # Выводит загруженные данные из файла
    print(data_loaded['employees']['Александр Костромичев'])
