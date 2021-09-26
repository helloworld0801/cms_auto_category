# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import ctypes
import importlib
import logging
import os
import sys
import time
import traceback
import winreg

import yaml

import lib.driver as g_ver_dr

from selenium import webdriver
from time import sleep


# 退出执行
def out():
    print('脚本结束将在3秒后退出')
    sleep(3)
    exit()


# 检测程序是否是超级管理员权限运行
def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class AutoBuild:

    # 初始化程序
    def __init__(self):
        # 初始变量
        self.config_file = 'config.yaml'
        self.config = {}
        self.web_file = 'web.yaml'
        self.web = {}
        self.gpath = 'google_path'
        self.gdriver = 'driver'
        # 是否有初始化
        self.is_init = False
        # 调试模式
        self.debug = False
        # 有无窗口运行
        self.window = False
        # 日志
        self.logger = logging.getLogger()

        if os.path.exists(self.web_file):
            f_web = open(self.web_file, 'r', encoding='utf-8')
            self.web = yaml.load(f_web, Loader=yaml.FullLoader)
            f_web.close()
        else:
            self.logger.info('站点配置文件不存在，请设置web.yaml文件，放入程序根目录')
            out()

        if os.path.exists(self.config_file):
            f_config = open(self.config_file, 'r', encoding='utf-8')
            self.config = yaml.load(f_config, Loader=yaml.FullLoader)
            f_config.close()
            if self.gpath not in self.config or self.gdriver not in self.config:
                # 配置文件信息不全，重新生成
                self.logger.info('配置文件信息不全')
                os.remove(self.config_file)
                self.config = self.ini_config()
        else:
            self.config = self.ini_config()

        if not self.config:
            out()

        # 如果未初始化，则检查驱动版本是否最新
        if not self.is_init:
            google_driver = self.up_google_driver()
            if not google_driver:
                out()
            # 驱动有更新，更新配置文件
            if google_driver != 1:
                self.config[self.gdriver] = google_driver
                f = open(self.config_file, 'w', encoding='utf-8')
                yaml.dump(self.config, f)
                f.close()

        # 是否开启debug模式
        if 'debug' in self.config and self.config['debug'] is True:
            self.debug = True

        # 是否开启debug模式
        if 'window' in self.config and self.config['window'] is True:
            self.window = True

    # 单线程模式
    def upcategory(self):

        site_dist = self.web
        # 启动浏览器
        path = 'chromedriver.exe'
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        if not self.window:
            # 无窗口运行
            chrome_options.add_argument('--headless')
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])

        # 开启浏览器
        _browser = webdriver.Chrome(executable_path=path, options=chrome_options)
        _browser.maximize_window()

        cms_dist = {}
        for sec in site_dist:
            data = dict(site_dist[sec])
            self.logger.info('----站点：' + sec + '，开始任务----')
            if data['type'] not in cms_dist:
                cms_dist[data['type']] = None
            if data['type'] in cms_dist:
                if not cms_dist[data['type']]:
                    try:
                        cms = importlib.import_module("lib.cms." + data['type'])
                        cms_dist[data['type']] = cms.CMS(_browser)
                    except ImportError:
                        self.logger.error('载入“' + data['type'] + '”包失败')
                        self._out_err()
                        self.logger.info('----站点：' + sec + '，提前结束任务----')
                        continue
                    except AttributeError:
                        self.logger.error('“' + data['type'] + '”包不存在启动方法')
                        self._out_err()
                        self.logger.info('----站点：' + sec + '，提前结束任务----')
                        continue
                    except Exception:
                        self.logger.error("发生错误")
                        self._out_err()
                        self.logger.info('----站点：' + sec + '，提前结束任务----')
                        continue
                try:
                    if not cms_dist[data['type']].begin(data):
                        self.logger.info('----执行失败，站点：' + sec + '，提前结束任务----')
                except AttributeError:
                    self.logger.error('“' + data['type'] + '”包不存在启动方法2')
                    self._out_err()
                    self.logger.info('----站点：' + sec + '，提前结束任务----')
                    continue
                except Exception:
                    self.logger.error("发生错误")
                    self._out_err()
                    self.logger.info('----站点：' + sec + '，提前结束任务----')
                    continue
            self.logger.info('----站点：' + sec + '，结束任务----')
        _browser.close()

    # 记录抛出的错误信息
    def _out_err(self):
        if self.debug:
            self.logger.warning('#########################################')
            self.logger.warning(traceback.format_exc())
            self.logger.warning('#########################################')

    # 通过注册表查询google安装地址
    def _get_chrome(self):
        # 定义检测位置
        sub_key = [r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                   r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall']

        software_name = []
        for i in sub_key:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, i, 0, winreg.KEY_ALL_ACCESS)
            for j in range(0, winreg.QueryInfoKey(key)[0] - 1):
                try:
                    key_name = winreg.EnumKey(key, j)
                    key_path = i + '\\' + key_name
                    each_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
                    DisplayName, REG_SZ = winreg.QueryValueEx(each_key, 'DisplayIcon')
                    DisplayName = DisplayName.encode('utf-8')
                    software_name.append(DisplayName)
                except WindowsError:
                    pass

        software_name = list(set(software_name))
        software_name = sorted(software_name)

        for item in software_name:
            if 'chrome.exe' in str(item, encoding="utf-8"):
                path_arr = str(item, encoding="utf-8").split(',')
                # 得到谷歌安装真实路径
                path = path_arr[0]
                config_dist = {}
                if os.path.exists(self.config_file):
                    f = open(self.config_file, 'r+', encoding='utf-8')
                    # 得到配置信息
                    config_dist = yaml.load(f, Loader=yaml.FullLoader)
                    config_dist[self.gpath] = path
                    yaml.dump(config_dist, f)
                    f.close()
                else:
                    f = open(self.config_file, 'w', encoding='utf-8')
                    config_dist[self.gpath] = path
                    yaml.dump(config_dist, f)
                    f.close()

    # 初始化配置
    def ini_config(self):
        self.is_init = True
        self.logger.info('开始执行初始化')
        self.find_google()
        sleep(3)
        config_dist = {}
        if os.path.exists(self.config_file):
            f = open(self.config_file, 'r+', encoding='utf-8')
            # 得到配置信息
            config_dist = yaml.load(f, Loader=yaml.FullLoader)
            if self.gpath in config_dist:
                self.logger.info('成功定位谷歌驱动')
                google_driver = self.up_google_driver(config_dist[self.gpath])
                if not google_driver:
                    f.close()
                    out()
                config_dist[self.gdriver] = google_driver
                yaml.dump(config_dist, f)
            else:
                self.logger.info('初始化失败,谷歌浏览器根地址不存在')
            f.close()
        else:
            self.logger.info('初始化失败,未能找到谷歌浏览器根地址')
        return config_dist

    # 更新google驱动
    def up_google_driver(self, google_path=''):
        if not self.is_init:
            google_path = self.config[self.gpath]
            driver_version = self.config[self.gdriver]
        else:
            driver_version = None
        # 得到谷歌浏览器版本
        google_version = g_ver_dr.getgoogleversion(google_path)
        # 匹配最佳版本
        driver_best_version = g_ver_dr.getdriverversion(google_version)
        if not driver_best_version:
            return 0
        # 当最佳驱动版本和当前驱动版本不一致，下载最新驱动版本
        if driver_version != driver_best_version:
            if not g_ver_dr.driverdown(driver_best_version):
                self.logger.info('驱动包下载失败')
                return 0
            # 驱动更新完毕
            return driver_best_version
        return 1

    # 如果查询不到google地址，则通过注册表获取google安装的位置
    def find_google(self):
        if _is_admin():
            self._get_chrome()
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 0)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # 创建一个handler，用于写入日志文件
    log_path = './logs'
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    rq = time.strftime('%Y%m%d', time.localtime(time.time()))
    logfile = log_path + '/' + rq + '.log'
    # 创建一个logger
    logger = logging.getLogger()
    # 设置文件记录日志格式
    format_str = logging.Formatter("%(asctime)s - %(module)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    # 设置屏幕输出日志格式
    win_format_str = logging.Formatter("%(message)s")
    # Log等级总开关
    logger.setLevel(logging.INFO)

    # 往屏幕上输出
    sh = logging.StreamHandler()
    sh.setFormatter(win_format_str)

    # 只输出info的信息
    sh_filter = logging.Filter()
    # 设置信息过滤等级
    sh_filter.filter = lambda record: record.levelno < logging.WARNING
    sh.addFilter(sh_filter)

    # 往文件里写入#指定间隔时间自动生成文件的处理器
    # 实例化TimedRotatingFileHandler
    # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
    # S 秒
    # M 分
    # H 小时、
    # D 天、
    # W 每星期（interval==0时代表星期一）
    # midnight 每天凌晨
    th = logging.FileHandler(logfile, mode='a')
    th.setFormatter(format_str)  # 设置文件里写入的格式

    logger.addHandler(sh)  # 把对象加到logger里
    logger.addHandler(th)

    # 日志初始化
    auto = AutoBuild()
    # 开始任务，单线程模式
    auto.upcategory()
