import datetime
import time
from datetime import date
import requests
from threading import Thread
import config

# ver0.3


api_key = config.api_key
url = config.url

areas = {10: '2,41,70,45,32,33,31', 3: '5,37,71,51,16,21,30', 9: '28,43,74,55,53,54,56', 4: '27,44,73,65',
         5: '14,42,72,66'}

data_areas = {}
employees = {}


# Сбор данных о заявках по районам
def collecting_data_by_area(area):
    today = date.today().strftime("%d.%m.%Y")
    area_all_task = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'get_list',
                                              'state_id': '1,3', 'type_id': areas[area]})

    area_close_task = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'get_list',
                                                'state_id': '2', 'type_id': areas[area],
                                                'date_finish_from': today})
    area_start = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'get_list',
                                           'state_id': '3', 'type_id': areas[area]})

    area_no_employee = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'get_list',
                                                 'state_id': '1,3', 'type_id': areas[area], 'employee_id': '-1'})

    data_areas[area] = [area_all_task.json()['count']]
    data_areas[area].append(area_close_task.json()['count'])
    data_areas[area].append(area_start.json()['count'])
    data_areas[area].append(area_no_employee.json()['count'])
    return data_areas


# Поиск имен мастеров по id
def masters_id_and_name(master_id):
    response = requests.get(url, params={'key': api_key, 'cat': 'employee', 'action': 'get_data',
                                         'id': master_id})
    master_name = response.json()['data'][str(master_id)]['name']  # получаем имя в запросе по id
    employees[master_name] = [master_id]  # >>> [запись]


# Список id мастеров
def masters_id():
    employee_id = []
    response = requests.get(url, params={'key': api_key, 'cat': 'employee', 'action': 'get_division', 'id': '27'})
    for i in response.json()['data']['27']['staff']['work']:  # запрашиваем все id в подразделении "27" (линейщики)
        i = i['employee_id']
        employee_id.append(i)
    main(masters_id_and_name, employee_id)


# Все заявки в исполнении, на которые назначен мастер
def application_data_task_start():
    today = date.today().strftime("%d.%m.%Y")

    for name in employees:
        # print('>>>', name, employees[name][0], end=': ')

        # Все заявки на которые назначен мастер
        response = requests.get(url, params={'key': api_key, 'cat': 'task',
                                             'action': 'get_list', 'state_id': '1,3',
                                             'employee_id': employees[name][0]})
        url_all = 'https://user.subnet05.ru/oper/?core_section=task_list&filter_selector0=task_staff_wo_division&' \
                  'employee_find_input=&employee_id0={}&filter_selector1=task_state&' \
                  'task_state1_value=995'.format(str(employees[name][0]))
        count_all = response.json()['count']
        employees[name].append([url_all, count_all])  # >>> [id, [запись]]
        # print('ALL', end=', ')

        # Все закрытые сегодня заявки на которые назначен мастер
        response = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'get_list', 'state_id': '2',
                                             'employee_id': employees[name][0], 'date_finish_from': today})
        url_close = 'https://user.subnet05.ru/oper/?core_section=task_list&filter_selector0=task_state' \
                    '&task_state0_value=2&filter_selector1=task_staff&employee_find_input=&employee_id1={id}' \
                    '&filter_selector2=date_finish&date_finish2_value2=3&date_finish2_date1={today}' \
                    '&date_finish2_date2={today}'.format(id=str(employees[name][0]), today=today)
        count_close = response.json()['count']
        employees[name].append([url_close, count_close])  # >>> [id, [all], [запись]]
        # print('CLOSE', end=', ')

        # запрос списка всех заявок в исполнении
        response = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'get_list', 'state_id': '3',
                                             'employee_id': employees[name][0]})
        count_start = response.json()['count']  # количестве заявок в исполнении >>> <int> 0-9
        task_start = response.json()['list'].split(',')  # список из номеров заявок >>> <list> [''] или ['53318']
        url_start = 'https://user.subnet05.ru/oper/?core_section=task_list&filter_selector0=task_staff&' \
                    'employee_find_input=&employee_id0={}&filter_selector1=task_state&' \
                    'task_state1_value=3'.format(str(employees[name][0]))

        employees[name].append([url_start, count_start, []])  # список с ссылкой, количеством заявок и списком из заявок
        if count_start > 0:  # если количество заявок больше нуля
            for task in task_start:
                url_task = 'https://user.subnet05.ru/oper/?core_section=task&action=show&id={}'.format(task)  # ...
                # ссылка на заявку

                # запрос инфы о заявке
                response = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'show', 'id': task})

                try:
                    login1 = response.json()['Data']['customer']['login']
                except KeyError:
                    login1 = ''

                try:
                    login2 = response.json()['Data']['additional_data']['47']['value']
                except KeyError:
                    login2 = ''

                try:
                    fio1 = response.json()['Data']['customer']['fullName']
                except KeyError:
                    fio1 = ''
                try:
                    fio2 = response.json()['Data']['additional_data']['36']['value']
                except KeyError:
                    fio2 = ''

                try:
                    address1 = response.json()['Data']['address']['text']
                    address1 = str(address1).replace('&#047;', '/')
                except KeyError:
                    address1 = ''

                try:
                    address2 = response.json()['Data']['additional_data']['38']['value']
                    address2 = str(address2).replace('&#047;', '/')
                except KeyError:
                    address2 = ''

                try:
                    description = [response.json()['Data']['type']['name'],
                                   response.json()['Data']['additional_data']['62']['value']]
                except KeyError:
                    description = [response.json()['Data']['type']['name'], '']

                # дата/время в заявке
                time_in_last_task = ['']  # время в последней заявке
                all_history_in_task = response.json()['Data']['history']  # собрать все изменения в заявке
                for history in all_history_in_task:  # пока одно изменение в заявке, то...
                    if history['type'] == 2 and history['param1'] == 3:  # если тип заявки "в испол" и параметр = 3, то
                        time_in_last_task[0] = history['date']

                year_r = int("".join(time_in_last_task).split()[0].split('-')[0])
                month_r = int("".join(time_in_last_task).split()[0].split('-')[1])
                day_r = int("".join(time_in_last_task).split()[0].split('-')[2])
                hours_r = int("".join(time_in_last_task).split()[1].split(':')[0])
                minutes_r = int("".join(time_in_last_task).split()[1].split(':')[1])
                date_then = datetime.datetime(year_r, month_r, day_r, hours_r, minutes_r)
                delta = datetime.datetime.now() - date_then
                if delta.days == 0:
                    time_data = str(delta).split(':')[0] + 'ч ' + str(delta).split(':')[1] + 'м'

                else:
                    time_data = str(delta.days) + 'д' + str(delta).split(',')[1].split(':')[0] + 'ч ' + \
                                str(delta).split(',')[1].split(':')[1] + 'м'

                time_in_last_task.append(time_data)
                employees[name][3][2].append(
                    [task, url_task, [login1, login2], [fio1, fio2], [address1, address2], description,
                     time_in_last_task])
        else:
            employees[name][3][2].append('no_task_start')
        # print('START', end=', ')

        # Время последней закрытой заявки
        week = (datetime.datetime.today() - datetime.timedelta(days=3)).strftime("%d.%m.%Y")  # дата неделю назад

        # запрос выполненных заявок за последнюю неделю
        response = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'get_list', 'state_id': '2',
                                             'employee_id': employees[name][0], 'date_finish_from': week})
        all_closed_task = response.json()['list'].split(',')  # список номеров выполненных заявок за последнюю неделю
        count_closed_task = response.json()['count']  # количество выполненных заявок за последнюю неделю

        # если список не пустой ...
        if count_closed_task > 0:
            employees[name].append([])
            for task in all_closed_task:  # заявка в списке заявок
                response = requests.get(url, params={'key': api_key, 'cat': 'task', 'action': 'show', 'id': task})
                employees[name][4].append([response.json()['Data']['date']['complete']])
            employees[name][4] = max(employees[name][4])
            employees[name][4] = str(employees[name][4][0]).split()
        else:
            employees[name].append(['no_closed_time'])
        # print('TIME', end=', ')

        # определяем тип блока
        # красный блок - исполнение заявки превысило 3 часа
        employees[name].append('')
        for tasks in employees[name][3][2]:
            if tasks != 'no_task_start':
                t = tasks[6][1].split()
                if len(t) == 3:
                    t_d = t[0].strip('д')
                    t_h = t[1].strip('ч')
                    t_m = t[2].strip('м')
                    second = (int(t_d) * 86400) + (int(t_h) * 3600) + (int(t_m) * 60)
                    max_time = 3600 * 3
                    if second > max_time:
                        employees[name][5] = 'block_task-maxtime'
                        break
                    else:
                        employees[name][5] = 'block_task-normal'
                if len(t) == 2:
                    t_h = t[0].strip('ч')
                    t_m = t[1].strip('м')
                    second = (int(t_h) * 3600) + (int(t_m) * 60)
                    max_time = 3600 * 3
                    if second > max_time:
                        employees[name][5] = 'block_task-maxtime'
                        break
                    else:
                        employees[name][5] = 'block_task-normal'
            else:
                employees[name][5] = 'block_task-notask'
        # print('TYPE', end='\n')

        # табель прихода мастера
        employees[name].append('')
        response = requests.get(url, params={'key': api_key, 'cat': 'employee', 'action': 'get_timesheet_data',
                                             'date_from': today, 'date_to': today, 'employee_id': employees[name][0]})
        at_work = str(response.json()['data']).replace('}}}', '').split(':')[-1].strip()

        if at_work == '[]':
            employees[name][6] = -1
        else:
            employees[name][6] = int(at_work)


def its_time():
    time_now = datetime.datetime.today()
    with open("time.txt", 'w') as file:
        file.write(time_now.strftime("%d-%m-%Y  %H:%M"))


def main(function, data):
    for d in data:
        th = Thread(target=function, args=(d,))
        th.start()
    time.sleep(0.5)


def start():
    # employees = {'name': [id, [all], [close], [start], last_time/'no_closed_time', div_type/'block_task-notask', at_work],
    #              'name2': [id2, ... ]}
    #   all = ['url', 'count']
    #   close = ['url', 'count']
    #   start = ['url', 'count', [task, task2, .../'no_task_start']]
    #       task = ['task_number', 'url', [login's], [surname's], [address's], [type_task, description],
    #              [date, time/'no_task_start']]

    # print('собираю данные о районах...')
    # main(collecting_data_by_area, areas)  # ШАПКА : инфа о заявках по районам
    print('собираю данные о мастерах по id...')
    masters_id()  # сбор всех id -> запись имён мастеров по id
    print('ждем 5 сек...')
    time.sleep(5)
    print('собираю данные о заявках мастеров...')
    application_data_task_start()  # инфа о всех заявках мастеров
    its_time()  # время запуска скрипта

    with open("employees.txt", 'w') as file:
        file.write(str(employees))

    with open("areas.txt", 'w') as file:
        file.write(str(data_areas))


while True:
    try:
        # print('*** СТАРТ')
        start()
        # print('/// ждем 10 сек между запросами')
        time.sleep(10)
        # print('')
    except:
        print('\nXXX ошибка соединения\n')
