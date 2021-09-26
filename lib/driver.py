import os
import re
import tempfile
import zipfile
import logging

import requests
import win32com.client
from requests import ReadTimeout


# 获取谷歌浏览器版本
def getgoogleversion(path=''):
    if not path:
        path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(path):
        parser = win32com.client.Dispatch("Scripting.FileSystemObject")
        return parser.GetFileVersion(path)
    else:
        return ''


# 得到driver版本信息
def getdriverversion(g_ver):
    logger = logging.getLogger()
    # 得到google driver所有版本信息
    domain = 'http://npm.taobao.org/mirrors/chromedriver/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    }
    try:
        get_response = requests.get(domain, headers=headers, params=None)
    except (ConnectionError, ReadTimeout):
        logger.error('版本信息拉取失败')
        return ''
    # google浏览器的版本分割（大版本，小版本）
    g_ver_list = g_ver.split('.')

    # 匹配相对应大版本的所有版本
    all_ver = re.findall('<a href="/mirrors/chromedriver/(' + g_ver_list[0] + '\.' + g_ver_list[1] + '\.[^/]*)',
                         get_response.text)

    if not len(all_ver):
        logger.info('查找不到当前谷歌浏览器的对应驱动版本1')
        return ''

    # 获取和子版本号一致或者低于的信息列表
    best_list = []
    down_dist = {}
    for item in all_ver:
        temp = item.split('.')
        if temp[2] == g_ver_list[2]:
            best_list.append(item)
        elif temp[2] < g_ver_list[2]:
            down_dist[temp[2]] = item

    if best_list:
        ret = best_list[len(best_list) - 1]
    elif down_dist:
        sorted(down_dist)
        down_list = down_dist.values()
        ret = down_list[len(down_list) - 1]
    else:
        logger.info('查找不到当前谷歌浏览器的对应驱动版本2')
        ret = ''
    return ret


# 下载相应驱动并解压
def driverdown(beta, path='./'):
    url = 'http://npm.taobao.org/mirrors/chromedriver/' + beta + '/chromedriver_win32.zip'
    try:
        response = requests.get(url)
    except (ConnectionError, ReadTimeout):
        return False
    data = response.content
    _tmp_file = tempfile.TemporaryFile()
    _tmp_file.write(data)
    zf = zipfile.ZipFile(_tmp_file, mode='r')
    zf.extractall(path)
    zf.close()
    return True
