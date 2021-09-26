# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import logging
import os
import re
import time

from time import sleep
from urllib.parse import urlparse
from urllib.parse import parse_qs
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class CMS:
    def __init__(self, browser: webdriver.Chrome = None):
        self.hash_name = None
        self.hash_val = None
        self.mine = False
        if not browser:
            # 启动浏览器
            path = 'chromedriver.exe'
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')

            # 开启浏览器
            browser = webdriver.Chrome(executable_path=path, options=chrome_options)
            browser.maximize_window()
            self.mine = True

        self._browser = browser
        self._browser.maximize_window()
        self._wait = WebDriverWait(self._browser, 10)
        # 日志
        self.logger = logging.getLogger()

    # 开始
    def begin(self, data):
        """更新栏目列表
        更新栏目列表的主体函数，所有操作流程都集合在这个函数里

        :param data: 配置字典，里面必须包含 login_url,category_url,username,password 等数据
        :return: bool
        """
        state = False
        # 开始登录
        if self._login(data['domain'] + data['login_url'], data['username'], data['password']):
            self.logger.info('登入成功,开始进入栏目更新')
        else:
            self.logger.info('登入失败')
            if self.mine:
                self.close()
            return state

        # 栏目更新页
        for cat in data['category']:
            if self._category(data['domain'] + cat['category_url']):
                self.logger.info(cat['mold'] + '栏目更新成功')
                state = True
            else:
                self.logger.info(cat['mold'] + '栏目更新失败')

        # 退出登录
        self._out(data['domain'] + data['out_url'])
        self.logger.info('退出登录')

        # 如果是类启动的浏览器，则关闭
        if self.mine:
            self.close()

        return state

    # 登录
    def _login(self, url, username, password):
        browser = self._browser
        wait = self._wait
        browser.get(url)
        wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys(username)
        wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        ).send_keys(password)
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "login_tj_btn"))
        ).click()
        sleep(3)
        wait.until(
            EC.presence_of_element_located((By.ID, "top_menu"))
        )
        # 获取页面地址信息
        domain_msg = urlparse(browser.current_url)
        # 判断是否成功登录
        test = re.search('^m=admin&c=index&pc_hash=(.*?)$', domain_msg.query)
        if domain_msg.path == '/index.php' and test:
            # 捕获pc_hash
            self.hash_name = 'pc_hash'
            self.hash_val = test.group(1)
            return True
        else:
            return False

    # 栏目页刷新
    def _category(self, url, img_path='./image'):
        browser = self._browser
        wait = self._wait
        # 请求信息
        request_msg = urlparse(url)
        browser.get(url + '&' + self.hash_name + '=' + self.hash_val)
        wait.until(
            EC.presence_of_element_located((By.NAME, "dosubmit1"))
        ).click()
        finish = False
        errnum = 0
        while 1:
            # 设置错误次数
            if errnum > 2:
                break
            sleep(5)
            domain_msg = urlparse(browser.current_url)
            test = re.search(request_msg.query + '&.*?' + self.hash_name + '=' + self.hash_val, domain_msg.query)
            if test and browser.title != '提示信息':
                finish = True
                self.logger.info('栏目生成结束,记录错误：' + str(errnum) + '次')
                break
            else:
                # content = browser.page_source
                domain_parse = parse_qs(browser.current_url)
                # 判断是否在刷新栏目列表
                if browser.title == '提示信息' and 'set_catid' in domain_parse and 'pagesize' in domain_parse:
                    self.logger.info('正在生成')
                else:
                    errnum += 1
                    today = time.strftime("%Y%m%d", time.localtime())
                    domain_msg = urlparse(browser.current_url)
                    path = img_path + '/' + domain_msg.hostname + '/' + today
                    os.makedirs(path, exist_ok=True)
                    file_name = '/' + str(int(time.time())) + '.png'
                    browser.save_screenshot(path + file_name)
                    self.logger.info('页面异常,已截图' + str(errnum) + '次')

        return finish

    def _out(self, url):
        self._browser.get(url)
        self._wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

    def close(self):
        self._browser.close()
