from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
import time
import requests
from bs4 import BeautifulSoup
import json
import fake_useragent
import datetime
import locale
import pandas as pd
from collections import defaultdict

locale.setlocale(locale.LC_TIME, "ru_RU")


# Функция получения списка заказов
def get_orders_names(login, password):
    # Логинимся в алике через селениум
    browser = webdriver.Chrome('/Users/feyn/Documents/Мои дурацкие творения/ali_orders/chromedriver')

    login_link = 'https://login.aliexpress.ru/'

    browser.get(login_link)

    time.sleep(2)

    # Передаем логин и пароль
    browser.find_element_by_id('fm-login-id').send_keys(login)
    browser.find_element_by_id('fm-login-password').send_keys(password)

    browser.find_element_by_xpath("//button[@type='submit']").click()

    time.sleep(2)

    # На случай просьбы подтверждения номера телефона
    try:
        browser.find_element_by_xpath("//button[@type='submit']").click()

        time.sleep(2)
    except NoSuchElementException:
        pass

    # Пока две попытки на загрузку заказов, если будет падать, допишу while
    try:
        browser.get('https://trade.aliexpress.ru/orderList.htm')

        time.sleep(2)

        browser.find_element_by_id('remiandTips_waitBuyerAcceptGoods').click()

    except NoSuchElementException:
        browser.get('https://trade.aliexpress.ru/orderList.htm')

        time.sleep(2)

        browser.find_element_by_id('remiandTips_waitBuyerAcceptGoods').click()

    # Получаем количество страниц с заказами
    pages_count = len(browser.find_elements_by_class_name('ui-goto-page')) - 1

    orders = list()
    names = list()

    # Собираем заказы и их названия в список
    for j in range(pages_count):

        page_orders = [i.text for i in browser.find_elements_by_class_name('info-body')][0::3]

        page_names = [i.text for i in browser.find_elements_by_xpath("//tbody[contains(@class, 'order-item-wraper')]"
                                                                     "/tr[@class='order-body'][1]"
                                                                     "//p[@class='product-title']/a")]

        orders += page_orders
        names += page_names

        time.sleep(2)

        if j != pages_count - 1:
            try:
                browser.find_element_by_xpath("//a[contains(text(), 'Вперёд')]").click()
            except NoSuchElementException:
                browser.find_element_by_xpath("//a[contains(text(), 'Next')]").click()

    # Передаем в реквестс параметры браузера после логина
    browser_cookies = browser.get_cookies()

    browser.close()

    session = requests.Session()
    c = [session.cookies.set(c['name'], c['value']) for c in browser_cookies]

    # Пробегаем по всем заказам и получаем номера отслеживания
    order_link = 'https://ilogisticsaddress.aliexpress.ru/ajax_logistics_track.htm?orderId='

    track_numbers = list()

    for order in orders:
        page = BeautifulSoup(session.get(order_link + order).text, 'html.parser')
        json_page = json.loads(str(page)[6:-1])
        track_number = json_page['tracking'][0]['mailNo'] if json_page['tracking'][0]['consoTagSecondMailNo'] == '' \
            else json_page['tracking'][0]['consoTagSecondMailNo']
        track_numbers.append(track_number)

    # На случай, если в один трек попало несколько заказов
    customs_test = defaultdict(list)

    for k, v in zip(track_numbers, names):
        customs_test[k].append(v)

    customs = dict()

    for key in dict(customs_test):
        others = 'и др.' if len(customs_test[key]) > 2 else ''
        customs[key] = ' '.join(customs_test[key][0].split()[:4]) if len(customs_test[key]) == 1 \
            else ' '.join(customs_test[key][0].split()[:4]) + ' + <br>' + ' '.join(customs_test[key][1].split()[:4]) \
                 + others

    # Записываем в файл, чтобы каждый раз не искать
    with open('customs.txt', 'w') as cus:
        json.dump(customs, cus)


# Функция получения статусов заказов
def get_orders_days():
    # Список статусов прибытия и получения
    arr_st = ['Package arrived to destination country', 'Прибыло на территорию России', 'Arrive at destination country',
              'Package arrived to destination airport', 'Arrival at Destination']

    end_st = ['Ожидает адресата в месте вручения', 'Прибыло в место вручения']

    # Создаем юзер агента
    user = fake_useragent.UserAgent().random
    headers = {'user-agent': user}
    session = requests.Session()

    link = 'https://1track.ru/ajax/tracking'

    # Достаем номера заказов
    with open('customs.txt', 'r') as cus:
        customs = json.load(cus)

    customs_df = pd.DataFrame(columns=['custom', 'key', 'China', 'Russia', 'last_status', 'delievered'])
    j = 0
    # Для каждого заказа подаем запрос остатусах и достаем последний статус, дни в России и дни в Китае
    for key in customs.keys():

        payload = {'tracks[0][track]': key}

        ses = session.post(link, headers=headers, data=payload).json()

        events = ses['JSON']['data']['events']

        length = len(events) - 1
        custom_name = customs[key]

        try:

            start_day = datetime.datetime.strptime(events[length]['date'], '%d %b %Y').date()
            that_day = datetime.date.today()

            for i in range(length, -1, -1):

                if events[i]['attribute'] in arr_st:
                    border_day = datetime.datetime.strptime(events[i]['date'], '%d %b %Y').date()
                    break
                else:
                    border_day = datetime.date.today()

            for i in range(length, -1, -1):

                if events[i]['attribute'] in end_st:
                    delievered = 1
                    break
                else:
                    delievered = 0

            customs_df.loc[j] = [custom_name, key, (border_day - start_day).days, (that_day - border_day).days,
                                 events[0]['attribute'], delievered]

        # На случай, если на сайте ничего нет про заказ
        except IndexError:
            customs_df.loc[j] = [custom_name, key, 0, 0, 'Пока нет информации о заказе', 0]
        j += 1

    return customs_df
