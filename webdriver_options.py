from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from exeptions import CreateException, AgentsException
from random import choice


class BaseOptions:
    def __init__(self, headless: bool = False, processes: int = 1):
        self.driver = None
        self._headless = headless  # Режим работы браузера (True - headless)
        self.processes = processes  # Количество потоков
        self._options()

    def create_driver(self):
        try:
            self.driver: WebDriver = webdriver.Chrome(options=self.options,
                                                      service=ChromeService(ChromeDriverManager().install()))
        except WebDriverException:
            raise CreateException

    def _options(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.options.add_argument('--start-maximized')
        try:
            with open('user_agent.txt', 'r', encoding='utf-8') as file:
                agents = [i.strip() for i in file.readlines()]
                user_agent = choice(agents)
                self.options.add_argument(f'user-agent={user_agent}')
                file.close()
        except IOError:
            raise AgentsException
        if self._headless:
            self.options.add_argument('--headless')
