import json
import aiohttp
import asyncio
import config
from datetime import datetime, timedelta
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

url = config.url
api = config.api_key
url_check = config.url_check
data = {}
divisions = '27,23'


class Master:
    def __init__(self, master_id):
        self.master_id = master_id
        self.name = ""
        self.timesheet = {}
        self.open_requests = 0
        self.in_progress_requests = 0
        self.closed_requests = 0
        self.closed_month_requests = 0
        self.page_url_open = ""
        self.page_url_in_progress = ""
        self.page_url_close = ""
        self.page_url_close_month = ""
        self.in_progress_requests_ids = []
        self.in_progress_requests_details = {}
        self.last_closed_request_time = ""


class DataService:
    def __init__(self, data_file):
        self.data_file = data_file
        self.session = None
        self.masters = {}

    @staticmethod
    async def get_datetime_requests():
        datetime_now = datetime.today()
        return datetime_now

    async def get_division(self):
        # асинхронный запрос к API для вывода id мастеров из подразделения "Монтажники/Линейщики"

        url_ = f'{url}key={api}&cat=employee&action=get_division&id={divisions}'
        employee_ids = []
        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                division = data['data']
                for division_id in division:
                    for employee in data['data'][division_id]['staff']['work']:
                        employee_ids.append(employee['employee_id'])
                        # break
                self.masters = {master_id: Master(master_id) for master_id in employee_ids}
                return self.masters
            else:
                raise Exception(f'API request failed with status: {response.status}')

    async def get_data(self, master_id):
        # асинхронный запрос к API для вывода имени мастера по id
        url_ = f'{url}key={api}&cat=employee&action=get_data&id={master_id}'
        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                return data['data'][str(master_id)]['name']
            else:
                raise Exception(f'API request failed with status: {response.status}')

    async def get_timesheet_data(self, master_id):
        # асинхронный запрос к API для вывода рабочего статуса мастера
        today = datetime.today()
        first_day = today.replace(day=1)
        next_month = first_day.replace(month=first_day.month + 1)
        last_day = next_month - timedelta(days=1)
        work_state = 0
        work_days = 0
        weekend_days = 0

        url_ = f'{url}key={api}&cat=employee&action=get_timesheet_data&date_from={first_day}&date_to={last_day}&employee_id={master_id}'
        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                for day in data['data']:
                    day_state_id = data['data'][day][str(master_id)]
                    value = next(iter(day_state_id.values()))

                    if today.strftime("%Y-%m-%d") == day:
                        work_state = value

                    if value.lower() in ["н", "в"]:
                        weekend_days += 1
                    else:
                        work_days += 1
                if today.strftime("%Y-%m-%d") not in data['data']:
                    work_state = -1
                return {'work_state': work_state, 'work_days': work_days, 'weekend_days': weekend_days}
            else:
                raise Exception(f'API request failed with status: {response.status}')

    async def assigned_application(self, master_id):
        # асинхронный запрос к API для вывода количества назначенных заявок и ссылки на страницу с фильтром
        url_ = f'{url}key={api}&cat=task&action=get_list&state_id=1,3&employee_id={master_id}'
        url_string = f'{url_check}/oper/?core_section=task_list&filter_selector0=task_staff_wo_division&employee_find_input=&employee_id0={master_id}&filter_selector1=task_state&task_state1_value=995'

        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                count = data['count']
                return count, url_string
            else:
                raise Exception(f'API request failed with status: {response.status}')

    async def applications_in_execution(self, master_id):
        # асинхронный запрос к API для вывода количества заявок в исполнении, ссылки на страницу с фильтром, словарь заявок и информации по ним
        url_ = f'{url}key={api}&cat=task&action=get_list&state_id=3&employee_id={master_id}'
        url_string = f'{url_check}/oper/?core_section=task_list&filter_selector0=task_staff&employee_find_input=&employee_id0={master_id}&filter_selector1=task_state&task_state1_value=3'

        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                count = data['count']
                tasks = data['list']
                tasks = tasks.split(',') if tasks else []
                return count, url_string, tasks
            else:
                raise Exception(f'API request failed with status: {response.status}')

    async def completed_today(self, master_id):
        # асинхронный запрос к API для вывода количества закрытых заявок за текущий день и ссылки на страницу с фильтром
        today = datetime.today()
        url_ = f'{url}key={api}&cat=task&action=get_list&state_id=2&employee_id={master_id}&date_finish_from={today.strftime("%d.%m-%Y")}&date_finish_to={today.strftime("%d.%m-%Y")}'
        url_string = f'{url_check}/oper/?core_section=task_list&filter_selector0=task_state&task_state0_value=2&filter_selector1=task_staff&employee_find_input=&employee_id1={master_id}&filter_selector2=date_finish&date_finish2_value2=3&date_finish2_date1={today.strftime("%d.%m-%Y")}&date_finish2_date2={today.strftime("%d.%m-%Y")}'

        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                count = data['count']
                return count, url_string
            else:
                raise Exception(f'API request failed with status: {response.status}')

    async def completed_month(self, master_id):
        # асинхронный запрос к API для вывода количества закрытых заявок за месяц и ссылки на страницу с фильтром
        today = datetime.today()
        first_day = today.replace(day=1)
        url_ = f'{url}key={api}&cat=task&action=get_list&state_id=2&employee_id={master_id}&date_finish_from={first_day.strftime("%d.%m-%Y")}&date_finish_to={today.strftime("%d.%m-%Y")}'
        url_string = f'{url_check}/oper/?core_section=task_list&filter_selector0=task_state&task_state0_value=2&filter_selector1=task_staff&employee_find_input=&employee_id1={master_id}&filter_selector2=date_finish&date_finish2_value2=9&date_finish2_date1={first_day.strftime("%d.%m-%Y")}&date_finish2_date2={today.strftime("%d.%m-%Y")}'

        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                count = data['count']
                return count, url_string
            else:
                raise Exception(f'API request failed with status: {response.status}')

    @staticmethod
    async def get_formatted_datetime(date_str):
        # Исходная строка "2024-04-24 16:41:15"
        date_parts = date_str.split()
        year, month, day = date_parts[0].split("-")
        hour, minutes, _ = date_parts[1].split(":")
        # Форматируем дату в "4-04-2024 16:41"
        formatted_date = f"{day}-{month}-{year} {hour}:{minutes}"
        return formatted_date

    @staticmethod
    async def get_deltatime(date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        current_datetime = datetime.now()
        delta = current_datetime - date_obj
        days = delta.days
        seconds = delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        # Форматируем результат
        if days:
            formatted_delta = f"{days}д {hours}ч {minutes:02d}м"
        else:
            formatted_delta = f"{hours}ч {minutes:02d}м"

        if delta.days > 0 or delta.seconds > 10800:  # 3 часа * 3600 секунд
            task_state = False
        else:
            task_state = True

        return formatted_delta, task_state

    async def customer(self, customer_ids: list) -> dict:
        """ Принимает на вход список id пользователей, и возвращает словарь с информацией о каждом пользователе (логин и ФИО) """
        resp = {}
        for customer_id in customer_ids:
            url_ = f'{url}key={api}&cat=customer&action=get_data&customer_id={customer_id}'
            async with self.session.get(url_) as response:
                if response.status == 200:
                    data = await response.json()
                    login = data['data']['login']
                    full_name = data['data']['full_name']
                    resp[customer_id] = {'login': login, 'full_name': full_name}
        return resp

    async def get_task_info(self, task_id):
        # Асинхронный запрос к API. Словарь заявок, где ключ - id заявки, значение - информация о заявке в исполнении по id заявки:
        # тип заявки, логин, ФИО, адрес и время когда заявка была назначена на мастера
        url_ = f'{url}key={api}&cat=task&action=show&id={task_id}'
        task_data = {'task_id': task_id,
                     'task_url': f'{url_check}/oper/?core_section=task&action=show&id={task_id}',
                     'task_datetime': '',
                     'task_deltatime': '',
                     'task_state': False,
                     'task_type': '',
                     'task_subtype': '',
                     'task_login_biling': '',
                     'task_login_oper': '',
                     'task_name_biling': '',
                     'task_name_oper': '',
                     'task_address_biling': '',
                     'task_address_oper': '', }
        if task_id:
            async with self.session.get(url_) as response:
                if response.status == 200:
                    data = await response.json()
                    history = data['data']['history']
                    for i in history:
                        if i['type_id'] == 575 and 'Добавлено' in i['comment']:
                            datetime_task = i['date']
                    task_data['task_datetime'] = await self.get_formatted_datetime(datetime_task)
                    task_data['task_deltatime'], task_data['task_state'] = await self.get_deltatime(datetime_task)
                    task_data['task_type'] = data['data']['type']['name']
                    try:
                        task_data['task_subtype'] = (data['data']['additional_data']['62']['value']).strip(
                            '[]').replace('\"', '')
                    except:
                        task_data['task_subtype'] = None

                    try:
                        # Проверяем, есть ли ключ 'customer' в data['data']
                        if 'customer' in data['data']:
                            customers = await self.customer(data['data']['customer'])
                            # Проверяем, что customers не пустой и содержит данные
                            if customers:
                                logins = [customer['login'] for customer in customers.values()]
                                full_names = [customer['full_name'] for customer in customers.values()]
                                task_data['task_login_biling'] = ', '.join(logins)
                                task_data['task_name_biling'] = ', '.join(full_names)
                        else:
                            # Если ключа 'customer' нет, устанавливаем значения в None
                            task_data['task_login_biling'] = None
                            task_data['task_name_biling'] = None

                    except KeyError as e:
                        # Обработка только KeyError (если ключ отсутствует)
                        print(f"KeyError: {e}")
                        task_data['task_login_biling'] = None
                        task_data['task_name_biling'] = None

                    except Exception as e:
                        # Обработка других исключений (если они возникнут)
                        print(f"An error occurred: {e}")
                        task_data['task_login_biling'] = None
                        task_data['task_name_biling'] = None


                    try:
                        task_data['task_login_oper'] = data['data']['additional_data']['47']['value']
                    except:
                        task_data['task_login_oper'] = None

                    # try:
                    #     # Добавил доп проверку на совпадение поля 'fullName' с логином из билинга или от оператора, т.к. когда нет поля 'login', в поле 'fullName' записывается логин из Билинга.
                    #     task_data['task_name_biling'] = data['data']['customer']['fullName'] if data.get('data') and \
                    #                                                                             data['data'].get(
                    #                                                                                 'customer') and \
                    #                                                                             data['data'][
                    #                                                                                 'customer'].get(
                    #                                                                                 'fullName') not in [
                    #                                                                                 task_data[
                    #                                                                                     'task_login_oper'],
                    #                                                                                 task_data[
                    #                                                                                     'task_login_biling']] else None
                    #     task_data['task_name_biling'] = task_data['task_name_biling'] if task_data[
                    #         'task_name_biling'] else None
                    # except:
                    #     task_data['task_name_biling'] = None

                    try:
                        task_data['task_name_oper'] = data['data']['additional_data']['36']['value'] if \
                            data['data']['additional_data']['36']['value'] else None
                    except:
                        task_data['task_name_oper'] = None

                    try:
                        task_data['task_address_biling'] = data['data']['address']['text'] if data['data']['address'][
                            'text'] else None
                        task_data['task_address_oper'] = str(task_data['task_address_oper']).replace('&#047;', '/')
                    except:
                        task_data['task_address_biling'] = None

                    try:
                        task_data['task_address_oper'] = data['data']['additional_data']['38']['value'] if \
                            data['data']['additional_data']['38']['value'] else None
                        task_data['task_address_oper'] = str(task_data['task_address_oper']).replace('&#047;', '/')
                    except:
                        task_data['task_address_oper'] = None

                    return task_data
                else:
                    raise Exception(f'API request failed with status: {response.status}')

    async def get_closed_time(self, task_id):
        url_ = f'{url}key={api}&cat=task&action=show&id={task_id}'

        async with self.session.get(url_) as response:
            if response.status == 200:
                data = await response.json()
                # print('### DATA GET_CLOSED_TIME', data['data']['date']['complete'])
                return datetime.strptime(data['data']['date']['complete'], "%Y-%m-%d %H:%M:%S")

    async def last_closed_task(self, master_id):
        # асинхронный запрос к API для вывода времени последней закрытой заявки из списка закрытых заявок по id мастера за последние 3 дня

        today = datetime.today()
        days_ago = today - timedelta(days=3)
        url_ = f'{url}key={api}&cat=task&action=get_list&state_id=2&employee_id={master_id}&date_finish_from={days_ago.strftime("%d.%m-%Y")}&date_finish_to={today.strftime("%d.%m-%Y")}'
        last_datetime = None

        async with self.session.get(url_) as response:
            try:
                if response.status == 200:
                    data = await response.json()
                    if data['count']:
                        for task_id in data['list'].split(','):
                            closed_datetime = await self.get_closed_time(task_id)
                            if not last_datetime:
                                last_datetime = closed_datetime
                            else:
                                last_datetime = closed_datetime if closed_datetime > last_datetime else last_datetime
                                # if closed_datetime is not None:
                                #     last_datetime = closed_datetime if closed_datetime > last_datetime else last_datetime
                                # else:
                                #     print('### CLOSED_DATETIME_NONE:', closed_datetime)
                                #     print('### LAST_DATETIME', last_datetime)
                                #     print('### MASTER_ID:', master_id)
                                #     print('### TASK_ID', task_id)

                        return last_datetime.strftime("%d-%m-%Y %H:%M")
                    else:
                        return None
                else:
                    raise Exception(f'API request failed with status: {response.status}')
            except:
                print('ПРОИЗОШЛА ОШИБКА!!!')
                print('### MASTER_ID:', master_id)

    async def update_master_info(self, master_id):
        master_obj = self.masters[master_id]

        # Делаем асинхронные запросы для каждого метода API.
        # Например, для получения данных о сотруднике:
        master_obj.name = await self.get_data(master_id)
        master_obj.timesheet = await self.get_timesheet_data(master_id)
        master_obj.open_requests, master_obj.page_url_open = await self.assigned_application(master_id)
        master_obj.in_progress_requests, master_obj.page_url_in_progress, master_obj.in_progress_requests_ids = await self.applications_in_execution(
            master_id)
        master_obj.closed_requests, master_obj.page_url_close = await self.completed_today(master_id)
        master_obj.closed_month_requests, master_obj.page_url_close_month = await self.completed_month(master_id)
        master_obj.in_progress_requests_details = {req_id: await self.get_task_info(req_id) for req_id in
                                                   master_obj.in_progress_requests_ids}
        master_obj.last_closed_request_time = await self.last_closed_task(master_id)

        # Обновляем данные о мастере в общем хранилище
        self.masters[master_id] = master_obj

    @retry(wait=wait_fixed(5), stop=stop_after_attempt(3), retry=retry_if_exception_type(aiohttp.ClientConnectorError))
    async def update_data(self):
        async with self.session.get(url_check) as response:
            if response.status == 200:
                # Получаем список ID мастеров
                master_ids = await self.get_division()

                # Обновляем информацию о каждом мастере
                await asyncio.gather(
                    *(self.update_master_info(master_id) for master_id in master_ids)
                )

                # Записываем обновленные данные в файл
                with open(self.data_file, 'w', encoding='utf-8') as file:
                    data['datetime'] = datetime.now().strftime("%d-%m-%Y %H:%M")
                    data['datetime_unix'] = int(datetime.now().timestamp())
                    data['employees'] = {master_id: master.__dict__ for master_id, master in self.masters.items()}
                    data['employees'] = dict(sorted(data["employees"].items(), key=lambda x: x[1]["name"]))
                    json.dump(data, file, ensure_ascii=False, indent=4)
            else:
                print('USERSIDE НЕДОСТУПЕН !!!')

    async def run(self):
        try:
            # Создаем сессию в асинхронном контексте
            async with aiohttp.ClientSession() as self.session:
                while True:
                    await self.update_data()
                    await asyncio.sleep(10)  # Пауза 10 сек перед следующим обновлением
        except aiohttp.ClientConnectorError as e:
            print(f"Failed to connect: {e}")
        finally:
            await self.session.close()


# Использование сервиса
data_service = DataService('data/data.json')
asyncio.run(data_service.run())


if __name__ == '__main__':
    pass
    # test = DataService(data_file='data/data2.json')
    # result = asyncio.run(test.get_task_info(221113))
    # print(result)
