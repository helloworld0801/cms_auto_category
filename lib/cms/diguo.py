# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import html
import os
import re
import time
import logging

from time import sleep
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class CMS:
    def __init__(self, browser: webdriver.Chrome = None):
        self.hash_name = None
        self.hash_val = None
        self.js_out = None
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
        self._wait = WebDriverWait(self._browser, 10)
        # 日志
        self.logger = logging.getLogger()

    # 开始
    def begin(self, data):
        """更新栏目列表
        更新栏目列表的主体函数，所有操作流程都集合在这个函数里

        :param data: 配置字典，里面必须包含 login_url,category_url,username,password 等数据
        :return: 无返回值
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
        self._out(data['domain'] + data['out_url'] + self.js_out)

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
            EC.presence_of_element_located((By.NAME, "imageField"))
        ).click()
        sleep(3)
        wait.until(
            EC.presence_of_element_located((By.ID, "frmTitle"))
        )
        # 获取页面地址信息
        domain_msg = urlparse(browser.current_url)
        # 判断是否成功登录
        test = re.search('^ehash_([^=]*?)=(.*?)$', domain_msg.query)
        if domain_msg.path == '/e/quan7-ad/admin.php' and test:
            # 捕获pc_hash
            self.hash_name = 'ehash_' + test.group(1)
            self.hash_val = test.group(2)

            # 获取内容,得到退出接口
            content = browser.page_source
            out_msg = re.search('enews\.php\?enews=exit&[^\'"]*', content)
            if out_msg:
                self.js_out = html.unescape(out_msg.group(0))
                self.logger.info('成功捕获退出链接')

            return True
        else:
            return False

    # 栏目页刷新
    def _category(self, url, img_path='./image'):
        browser = self._browser
        wait = self._wait
        browser.get(url + '?' + self.hash_name + '=' + self.hash_val)
        jump_js = wait.until(
            EC.presence_of_element_located((By.NAME, "Submit22"))
        ).get_attribute('onclick')
        jump_url = re.search("window\.open\('([^']*?)'", jump_js).group(1)
        js = 'window.location.href = "' + jump_url + '"'
        browser.execute_script(js)
        finish = False
        errnum = 0
        while 1:
            # 设置错误次数
            if errnum > 2:
                self.logger.error('异常超出次数范围，已停止栏目更新')
                break
            sleep(5)
            domain_msg = urlparse(browser.current_url)
            if domain_msg.path == '/e/quan7-ad/ReHtml/ChangeData.php':
                finish = True
                self.logger.info('栏目生成结束,记录错误：' + str(errnum) + '次')
                break
            else:
                # 判断是否在刷新栏目列表
                if browser.title.strip() == '' and domain_msg.path == '/e/quan7-ad/ecmschtml.php':
                    self.logger.info('正在生成')
                elif browser.title.strip() == '信息提示' and domain_msg.path == '/e/quan7-ad/ecmschtml.php':
                    tip_msg = browser.find_element_by_tag_name('b')
                    if tip_msg and tip_msg.text.strip() == '刷新所有信息列表成功':
                        self.logger.info('栏目列表刷新完毕')
                    else:
                        path = img_path + '/' + domain_msg.hostname
                        self._save_screen(path)
                else:
                    errnum += 1
                    path = img_path + '/' + domain_msg.hostname
                    self._save_screen(path)

        return finish

    def _out(self, url):
        self._browser.get(url)
        self._wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

    def _save_screen(self, img_path):
        today = time.strftime("%Y%m%d", time.localtime())
        path = img_path + '/' + today
        os.makedirs(path, exist_ok=True)
        file_name = '/' + str(int(time.time())) + '.png'
        self._browser.save_screenshot(path + file_name)

    def close(self):
        self._browser.close()
