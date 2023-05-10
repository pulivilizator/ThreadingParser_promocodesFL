from webdriver_options import BaseOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import Keys
from selenium.common.exceptions import NoSuchElementException
from exeptions import ShopExeption
import csv
import threading
import multiprocessing
import time


class DataScraper(BaseOptions):
    def __init__(self, headless: bool, processes=1):
        super().__init__(headless, processes)
        self.c = 0
        self.pool = None
        self.hrefs = None
        self.hrefs_reform = None

    def scrape_shops(self):
        """Собирает список магазинов"""

        try:
            print('Сбор магазинов\n')
            with self.driver as browser:
                browser.get('https://www.rezeem.com/stores')
                category = browser.find_elements(By.CLASS_NAME, 'column.is-12')
                self.hrefs = [j.get_attribute('href') for i in category[1:] for j in i.find_elements(By.TAG_NAME, 'a')]
                browser.quit()
        except NoSuchElementException:
            raise ShopExeption
    @staticmethod
    def split_list(lst: list, n) -> list:
        """Разделяет список на n подсписков."""

        length = len(lst)
        size = length // n
        remainder = length % n
        result = []
        start = 0
        for i in range(n):
            if i < remainder:
                end = start + size + 1
            else:
                end = start + size
            result.append(lst[start:end])
            start = end
        return result
    @staticmethod
    def process_sublist(sublist: list) -> list:
        """Обрабатывает подсписок."""

        result = []
        for item in sublist:
            result.append(item)
        return result

    def reformat(self):
        """Разбивает список на подсписки и обрабатывает их параллельно."""

        print('Формирование списков\n')
        sublists = self.split_list(self.hrefs, self.processes)
        with multiprocessing.Pool(processes=self.processes) as pool:
            self.hrefs_reform = pool.map(self.process_sublist, sublists)

    def _parser(self, hrefs: list[str, ...]):
        with self.pool:
            with webdriver.Chrome(options=self.options) as browser:
                for href in hrefs:
                    print(href)
                    browser.get(href)
                    time.sleep(3)
                    url = href
                    name = browser.find_element(By.CLASS_NAME, 'title.is-6.mb-2').text.split('Rate ')[1]
                    photo = browser.find_element(By.CLASS_NAME, 'st-logo').get_attribute('src')
                    coupons = []
                    for i in ['ocode', 'odeal']:
                        [coupons.append(j) for j in
                         browser.find_elements(By.CLASS_NAME, f'coupon.c-filt.cp-exclusive.{i}.show')]
                        [coupons.append(j) for j in
                         browser.find_elements(By.CLASS_NAME, f'coupon.c-filt.{i}.show')]
                        coupons = list(set(coupons))
                    if coupons:
                        for i in range(len(coupons)):
                            button = coupons[i].find_element(By.CLASS_NAME, 'subtitle')
                            coupons[i].find_element(By.CLASS_NAME, 'cp-desc-togl').click()
                            descr = coupons[i].find_element(By.CLASS_NAME, 'cp-desc.content.column').text
                            ActionChains(browser).move_to_element(button).click().perform()
                            time.sleep(5)
                            browser.implicitly_wait(3)
                            windows = browser.window_handles
                            browser.switch_to.window(windows[1])
                            post_redirect = browser.current_url
                            browser.close()
                            browser.switch_to.window(windows[0])

                            coupon_url = browser.current_url
                            after_redirect = browser.find_element(By.CLASS_NAME, 'cp-pop-next').get_attribute('href')
                            promocode = browser.find_element(By.CLASS_NAME, 'tag.cp-popcode').text.strip()
                            if promocode == 'Deal Activated':
                                promocode = ''
                                name_shop = name
                            else:
                                name_shop = browser.find_element(By.CLASS_NAME, 'has-text-primary').text

                            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                            coupons = []
                            for m in ['ocode', 'odeal']:
                                [coupons.append(j) for j in
                                 browser.find_elements(By.CLASS_NAME, f'coupon.c-filt.cp-exclusive.{m}.show')]
                                [coupons.append(j) for j in
                                 browser.find_elements(By.CLASS_NAME, f'coupon.c-filt.{m}.show')]
                                coupons = list(set(coupons))
                            f = url, name, photo, coupon_url, name_shop, descr, promocode, after_redirect, post_redirect
                            with open('data.csv', 'a', encoding='utf-8-sig', newline='') as file:
                                writer = csv.writer(file, delimiter=';')
                                writer.writerow(f)

    def main(self):
        with open('data.csv', 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['Основной URL', 'Название магазина', 'Файл логотипа', 'Урл на купонном сайте', 'Название магазина',
                             'Заголовок акции и описание акции', 'Промокод', 'URL открываемого магазина до редиректа',
                             'URL открываемого магазина после редиректа'])

        self.pool = threading.BoundedSemaphore(value=self.processes)
        for url_list in self.hrefs_reform:
            threading.Thread(target=self._parser, args=(url_list,)).start()

