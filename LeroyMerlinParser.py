# Основной модуль
import csv
import json
import os
import re
import time
from datetime import datetime
from time import time as it
from typing import List, Dict, Tuple

import requests
from art import tprint
from bs4 import BeautifulSoup
from colorama import init, Fore
from loguru import logger
from playsound import playsound

init()
if not os.path.isdir('items'): os.mkdir('items')
LOG_FMT = '{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | func: {function: ^15} | line: {line: >3} | message: {message}'
logger.add(sink='logs/debug.log', format=LOG_FMT, level='INFO', diagnose=True, backtrace=False,
           rotation="100 MB", retention=2, compression="zip")


class ConfigData:
    encoding_resBase = 'utf-8-sig'
    signal_file = os.path.abspath('items/signal.mp3')
    csv_file = os.path.abspath('LeroyBase.csv')
    headers_file = os.path.abspath('items/headers.json')
    catalog_file = os.path.abspath('items/catalog.json')

    dev = 'https://github.com/MalakhovStas'
    X_API_KEY = 'VY0AKH3eBwhyGUjBM5U9rO4PyBvTG0cA'
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8," \
             "application/signed-exchange;v=b3;q=0.9"

    HOST = 'https://leroymerlin.ru'
    URL_catalog = 'https://leroymerlin.ru/catalogue/'
    URL_api = 'https://api.leroymerlin.ru/aem_api/v1/getProductAvailabilityInfo'

    REGION_id = '34'  # 34 - Москва и область
    not_categories = []


class ExcStopParsing(Exception):
    pass


class BadStatusCode(Exception):
    pass


class GetAccess:
    __alph = {1: '%OrAHkYvUD', 2: '$GoSQnwxhf', 3: '&LigydCKbu', 4: '@tjzEVBaPZ', 5: '~NmJcqlXRp'}
    __access_file = os.path.abspath('items/a_file.txt')

    @classmethod
    def __access(cls, key: str) -> str | None:
        staff = []
        key = list(key)
        result = []
        for index, i_k in enumerate(key):
            if (index + 1) % 6 == 0 and i_k not in ConfigData.dev[19:22] + ConfigData.dev[27:29]:
                return None
            if index == 0 or index % 6 == 0:
                result.append(i_k)
        for i_r in result:
            for i_a in cls.__alph.values():
                for i_nd, i_z in enumerate(list(i_a)):
                    if i_r == i_z:
                        staff.append(i_nd)

        staff = int(''.join(map(str, staff)))
        if staff < it():
            print(f'{Fore.RED}Ключ не актуален', Fore.RESET)
            return None
        if (staff - it()) < 260000:
            print(f'{Fore.RED}Внимание Ваш ключ действителен до:',
                  Fore.YELLOW, datetime.utcfromtimestamp(staff).strftime('%d.%m.%Y'),
                  f'\nЗапросите ключ доступа у разработчика: {Fore.BLUE}{ConfigData.dev}', Fore.RESET)
        return 'ok'

    @classmethod
    def get_access(cls) -> bool:
        if os.path.isfile(cls.__access_file):
            with open(cls.__access_file, 'r') as file:
                key = file.readlines()
            if cls.__access(key[0].strip()[::-1]) == 'ok':
                return True

            elif key[-1].isdigit() and int(key[-1]) > it():
                tm = datetime.utcfromtimestamp(int(key[-1]) - it()).strftime('%M мин %S сек')
                print(f'{Fore.RED}Доступ к приложению ограничен на {tm} мин, '
                      f'запросите ключ доступа у разработчика: '
                      f'{Fore.BLUE}{ConfigData.dev}', Fore.RESET)
                time.sleep(10)
                return False

        for index, step in enumerate(range(5)):
            key = input('Введите ключ доступа к приложению: ').strip()
            if len(key) == 60 and cls.__access(key) == 'ok':
                with open(cls.__access_file, 'w') as file:
                    file.write(key[::-1])
                return True
            print(f'{Fore.YELLOW}Неизвестный ключ', Fore.RESET)
            if index < 4:
                print(f'{Fore.RED}Осталось попыток {5 - (index + 1)}', Fore.RESET)
            else:
                print(
                    f'{Fore.RED}Доступ к приложению ограничен на 10 мин, запросите ключ доступа у разработчика: '
                    f'{Fore.BLUE}{ConfigData.dev}', Fore.RESET)
        else:
            with open(cls.__access_file, 'a') as file:
                file.write('\n' + str(int(it() + 600)))
        return False


class SaveData:

    @staticmethod
    def start_file_save(path: str) -> None:
        rez = input(f'\n{Fore.RED}Перезаписать файл введите {Fore.RESET}- 1 {Fore.GREEN}| '
                    f'{Fore.YELLOW}Добавить данные в файл нажмите {Fore.RESET}- Enter: ').lower() \
            if os.path.isfile(ConfigData.csv_file) else '1'

        if rez == '1':
            with open(path, 'w', newline='', encoding=ConfigData.encoding_resBase) as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(['Наименование товара', 'Ссылка на товар', 'Остаток товара в регионе'])
                logger.debug(f'Файл {ConfigData.csv_file} создан')

    @staticmethod
    def save_data(data: Dict, path: str) -> None:
        MiscUtils.get_signal()
        while True:
            time.sleep(0.5)
            next_stage = input(f'\n{Fore.YELLOW}Добавить данные в файл?{Fore.RESET} - y / n ').lower()
            if next_stage == 'y':
                break
            elif next_stage == 'n':
                return
            time.sleep(0.5)
            print(f'{Fore.RED}Ошибка ввода, нужно ввести - y или - n', Fore.RESET)

        with open(path, 'a', newline='', encoding=ConfigData.encoding_resBase) as file:
            writer = csv.writer(file, delimiter=';')
            for key, values in data.items():
                writer.writerow([key])
                for i_key, value in values.items():
                    writer.writerow([i_key, value[0], value[1]])
        logger.info(f'Данные успешно сохранены в файл: {ConfigData.csv_file}')


class MiscUtils:
    __base_signal = ConfigData.signal_file

    @classmethod
    def get_signal(cls) -> None:
        try:
            if os.path.isfile(cls.__base_signal):
                playsound(cls.__base_signal, block=False)
        except Exception:
            pass

    @classmethod
    def end_work(cls, result: str) -> None:
        time.sleep(0.5)

        if result == 'BAD':
            print(f'\n{Fore.RED}Парсинг данных с сайта {ConfigData.HOST} завершился критической ошибкой, '
                  f'данные получены не в полном объёме{Fore.RESET}')

        else:
            print(f'\n{Fore.GREEN}Парсинг данных с сайта {ConfigData.HOST} '
                  f'выполнен корректно, данные получены в полном объёме', Fore.RESET)

        time.sleep(1)
        print(f'\n{Fore.GREEN}Разработано: {Fore.BLUE}{ConfigData.dev}', Fore.RESET)
        cls.get_signal()
        input(f'{Fore.YELLOW}Для завершения работы нажмите -{Fore.RESET} Enter')
        time.sleep(1)

    @classmethod
    def choice_next_stage(cls, key: str) -> str:
        while True:
            time.sleep(0.5)
            next_stage = input(f'\n{Fore.YELLOW}Продолжить парсинг{Fore.RESET} - y / n ').lower()
            if next_stage == 'y':
                if not key in ConfigData.not_categories:
                    ConfigData.not_categories.append(key)
                stage = 'next'
                break
            elif next_stage == 'n':
                stage = 'stop'
                break
            time.sleep(0.5)
            print(f'{Fore.RED}Ошибка ввода, нужно ввести - y или - n', Fore.RESET)
        return stage

    @classmethod
    def restart_parse_page(cls, page: int, end_url: str) -> Tuple[str, int] | Tuple[None, int]:
        cls.get_signal()
        while True:
            time.sleep(0.5)
            rst = input(f'\n{Fore.YELLOW}Перезапустить парсинг со страницы: {Fore.GREEN}{page}{Fore.RESET} - y / n ').lower()
            if rst == 'y':
                return end_url, page - 1
            elif rst == 'n':
                return None, page
            time.sleep(0.5)
            print(f'{Fore.RED}Ошибка ввода, нужно ввести - y или - n', Fore.RESET)


class Utils:

    @staticmethod
    def get_headers(url: str) -> None:
        while True:
            MiscUtils.get_signal()
            time.sleep(0.5)
            c_keys = input(f'{Fore.YELLOW}Введите ключи: {Fore.RESET}').strip()

            hed = {"accept": ConfigData.ACCEPT, "cookie": c_keys, "user-agent": ConfigData.USER_AGENT}

            html = requests.get(url, headers=hed)
            headers_data = dict(html.request.headers) if html.status_code == 200 else {}
            if headers_data.get("cookie"):
                logger.debug(f'Ключи верные, статус ответа: OK')
                with open(ConfigData.headers_file, 'w') as file:
                    json.dump(headers_data, file)
                    return
            else:
                logger.error(f'Ключи устарели или введены некорректные данные, статус ответа: {html.status_code}')

    @staticmethod
    def get_html(url: str, params: str | dict = '', num_request=[0], step=1) -> requests.models.Response | None:
        try:
            num_request[0] += 1
            if not os.path.isfile(ConfigData.headers_file):
                logger.warning('Файл с ключами не найден -> создаю схему зависимостей ...')
                Utils.get_headers(ConfigData.URL_catalog)

            with open(ConfigData.headers_file, 'r') as file:
                headers = json.load(file)

            logger.debug(f'Запрос #{num_request[0]}')
            html = requests.get(url, headers=headers, params=params)

        except Exception as exc:
            logger.error(f'Ошибка при запросе к сайту: {exc}, return-> html = None')
            html = None

        else:
            if html.status_code == 200:
                logger.debug(f'Статус ответа: OK')

                headers_data = dict(html.request.headers)
                if headers_data.get("cookie"):
                    with open(ConfigData.headers_file, 'w') as file:
                        json.dump(headers_data, file)
                    logger.info(f'Ключи обновлены')

            else:
                logger.warning(f'Доступ к сайту заблокирован -> необходимо обновить ключи')
                Utils.get_headers(ConfigData.URL_catalog)
                if step == 1:
                    logger.warning(f'Повторяю запрос')
                    html = Utils.get_html(url=url, params=params, step=2)
                    logger.info(f'Успешно, статус: OK') if html.status_code == 200 \
                        else logger.error(f'Доступ к сайту заблокирован')
                else:
                    logger.error(
                        f'Ошибка повторного запроса, статус ответа: {html.status_code} -> return -> html = None')
                    html = None

        finally:
            return html

    @staticmethod
    def get_catalogue(html: str) -> Dict:
        catalog = {}
        soup = BeautifulSoup(html, 'html.parser')
        head_items = soup.find_all('div', class_='section-card')

        for index, item in enumerate(head_items):
            i_title = item.find_next('div', class_='title').find('a').get_text(strip=True) + f'={index + 1}'
            i_link = ConfigData.HOST + item.find_next('div', class_='title').find('a').get('href')
            catalog[i_title + ';' + i_link] = []
            sub_items = item.find_all('li')

            for i_index, value in enumerate(sub_items):
                if i_index == len(sub_items) - 1:
                    continue
                value_title = value.find_next('span', class_='section-card-text').get_text(
                    strip=True) + f'={i_index + 1}'
                value_link = ConfigData.HOST + value.find_next('a').get('href')
                catalog[i_title + ';' + i_link].append(value_title + ';' + value_link)

        with open(ConfigData.catalog_file, 'w') as file_cat:
            json.dump(catalog, file_cat)

        logger.info(f'Каталог успешно обновлён, основных разделов: {len(catalog)} ')
        return catalog

    @staticmethod
    def get_min_stock() -> int:
        stc = 'start'
        while isinstance(stc, str):
            stc = input(f"\n{Fore.YELLOW}Введите минимальное количество остатков товара для выгрузки:"
                        f"{Fore.RESET} ").strip()
            stc = int(stc) if stc.isdigit() else 'restart'

        return stc

    @staticmethod
    def get_stock(product_id: str, step=1, num=[0]) -> int | float:
        try:
            num[0] += 1
            smm = 0

            headers = {'user-agent': ConfigData.USER_AGENT, 'x-api-key': ConfigData.X_API_KEY}
            payload = {'productId': product_id, 'productSource': 'E-COMMERCE', 'regionId': ConfigData.REGION_id}

            response = requests.post(ConfigData.URL_api, headers=headers, json=payload)
            logger.debug(
                f'Запрос к api #{num[0]}, статус: {"OK" if response.status_code == 200 else response.status_code}')

            if response.status_code != 200:
                raise BadStatusCode

            stores = response.json().get('stores')
            if stores:
                for store in stores.values():
                    stock = store['stock']
                    if stock and isinstance(stock, (int, float)):
                        smm += stock
                    smm = round(smm, 2) if isinstance(smm, float) else smm
            return smm

        except Exception as exc:
            if step == 1:
                logger.warning(f'Ошибка запроса к api  -> повторяю запрос')
                result = Utils.get_stock(product_id, step=2)
                if result != 0:
                    logger.info(f'Успешно, остаток товара: {result}')

                return result

            else:
                logger.error(f'Ошибка повторного запроса к api -> return -> остаток товара: 0, ошибка: {exc}')
                return 0

    @staticmethod
    def choice_category(catalog: Dict[str, List[str]] | List[str], not_categories: List, step='first') -> Dict:
        new_catalog = {}
        i_iter = catalog.keys() if step == 'first' else catalog

        names = []
        for i_key in i_iter:
            name = i_key.split(';')[0].split('=')[0]
            names.append(len(name))
        height = str(max(names)) + 's'

        line = '\n'
        for i_key in i_iter:
            category, link = i_key.split(';')
            name, key = category.split('=')
            sep = '    ' if int(key) % 3 != 0 else '\n'
            if name in not_categories:
                line += f'{Fore.MAGENTA}{name:{height}} - {key:2s}{Fore.RESET}' + sep
            else:
                line += f'{Fore.YELLOW}{name:{height}}{Fore.RESET} - {key:2s}' + sep
            new_catalog[name] = link
        line += f'{Fore.YELLOW}Все разделы{Fore.RESET} - 0'

        while True:
            time.sleep(1)
            choice = input(f'{line}\n\nВведите номер раздела для парсинга: ')

            if choice == '0':
                print(f'\n{Fore.WHITE}Выбраны все разделы{Fore.RESET}')
                time.sleep(1)
                return new_catalog

            elif choice.isdigit() and int(choice) in range(0, len(i_iter) + 1):
                for cat in i_iter:
                    if cat.split(';')[0].split('=')[1] == choice:
                        name_category = ''.join(tuple(cat.split(';')[0])).rstrip(f"={choice}")
                        link_category = cat.split(';')[1]
                        print(f'\nВыбран раздел:', f'{Fore.WHITE}{name_category}{Fore.RESET}')
                        time.sleep(1)

                        result = Utils.choice_category(catalog[cat], step='second', not_categories=not_categories) \
                            if step == 'first' else {name_category: link_category}

                        return result
            else:
                print(f'{Fore.RED}Ошибка ввода, попробуйте ещё раз', Fore.RESET)

    @staticmethod
    def get_next_page(page_soup: BeautifulSoup) -> Tuple[str] | None:
        items = page_soup.find_all('a', class_='bex6mjh_plp s15wh9uj_plp l7pdtbg_plp r1yi03lb_plp sj1tk7s_plp')
        result = None
        for item in items:
            check = re.search(r'data-qa-pagination-item=\"right\"', str(item))
            if check and check.group() == 'data-qa-pagination-item="right"':
                result = (item.get('aria-label'), ConfigData.HOST + str(item.get('href')))
        return result


class Parser:

    @staticmethod
    def parser() -> None:

        print(f'{Fore.GREEN}Разработано: {Fore.BLUE}{ConfigData.dev}', Fore.RESET)
        if not GetAccess.get_access():
            return
        pages = {}
        stage = 'start'
        tprint(f'Parser - LeroyMerlin')
        time.sleep(0.5)
        SaveData.start_file_save(ConfigData.csv_file)
        time.sleep(0.5)
        stc = Utils.get_min_stock()
        html = Utils.get_html(ConfigData.URL_catalog)

        try:
            while stage != 'stop':
                catalog = Utils.choice_category(Utils.get_catalogue(html.text),
                                                not_categories=ConfigData.not_categories)

                for defkey, url_link in catalog.items():
                    key = defkey.split("=")[0]
                    logger.info(f'Парсинг раздела: {key}')
                    fact_page, num_page = 0, 0
                    pages[key] = {}

                    while url_link:
                        num_page += 1
                        new_html = Utils.get_html(url_link, params={'page': num_page})

                        if new_html is None:
                            raise ExcStopParsing

                        fact_page = int(new_html.url.split('=')[1]) if new_html.url.split('=')[1].isdigit() else 0

                        # Дополнительная проверка
                        if fact_page < num_page:
                            url_link = None
                            logger.warning(f'Парсинг раздела: {key} успешно завершён Тута')
                            continue
                        # По идее срабатывать не должна

                        logger.debug(f'Парсинг страницы {fact_page}, раздел: {key}, ссылка: {new_html.url}')

                        soup = BeautifulSoup(new_html.text, 'html.parser')
                        items = soup.find_all('div', class_='phytpj4_plp largeCard')
                        for item in items:
                            if item:
                                link = item.find_next('a').get('href')
                                article = link[-9:-1]
                                nums = Utils.get_stock(product_id=article) if article.isdigit() else 0

                                if nums >= stc:
                                    pages[key][item.find_next('a').get('aria-label')] = ConfigData.HOST + link, nums
                                logger.debug(f'артикул: {article}, остаток: {nums}, ссылка: {ConfigData.HOST + link}') \
                                    if nums == 0 else logger.debug(f'артикул: {article}, остаток: {nums}')

                        next_page = Utils.get_next_page(page_soup=soup)
                        if not next_page is None:
                            logger.debug(f'{next_page[0]}, ссылка: {next_page[1]}')
                        else:
                            logger.info(f'Парсинг раздела: {key} завершён успешно, последняя страница: {fact_page}')
                            url_link, num_page = MiscUtils.restart_parse_page(fact_page, url_link)

                    logger.info(f'Проверено страниц: {fact_page}, кол-во товаров: {len(pages[key])}')

                    SaveData.save_data(pages, ConfigData.csv_file)
                    pages.clear()

                    stage = MiscUtils.choice_next_stage(key)
            MiscUtils.end_work(result='Ok')

        except Exception as exc:
            logger.error(f'Критическая ошибка: {exc}')
            logger.warning(f'Парсинг раздела {key} завершён не полностью, '
                           f'проверено страниц: {fact_page} '
                           f'кол-во товаров: {len(pages[key])}')

            SaveData.save_data(pages, ConfigData.csv_file)
            MiscUtils.end_work(result='Bad')


if __name__ == '__main__':
    os.system("mode con cols=200 lines=40")
    Parser.parser()
