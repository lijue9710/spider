import requests
import time
import os
import pdb
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.chrome.options import Options

import json
import csv
import re

from urllib import request
import urllib
import sys
from datetime import datetime
import socket
import pandas as pd

# 加载chrome驱动
options = webdriver.ChromeOptions()
options.add_argument('lang=zh_CN.UTF-8')
# 无头模式
# options.add_argument('--headless')
# chromedriver.exe的路径
driver_path = 'C:\Program Files\Google\Chrome\Application\chromedriver'
driver = webdriver.Chrome(executable_path=driver_path, options=options)


# 翻页：url拼接page_number
def spider_by_page(target):
    driver.get(target)
    time.sleep(5)
    pages = driver.find_element_by_class_name('last').find_element_by_tag_name('a').get_attribute('data-page')
    print('共' + pages + '页')

    regex_info = re.compile(r'[:：]+')
    regex_filename = re.compile(r'Name=([\s\S]*?)&')

    # 写入csv
    fieldnames = ['title', 'download_link', 'detail_page', 'number', 'type', 'language', 'date', 'version',
                  'product_name', 'file_name']
    with open('schneider_csv.csv', 'ab', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        # 遍历页面
        for i in range(25, int(pages) + 1):  # int(pages) + 1
            list_items = []
            print('当前为第', i, '页')
            page = target + '&pageNumber=' + str(i)

            driver.execute_script("window.open('" + page + "');")
            # 获取浏览器所有标签的句柄，返回列表
            handles = driver.window_handles
            # 切换到新的标签页
            driver.switch_to.window(handles[-1])
            time.sleep(5)

            items = driver.find_elements_by_class_name('result-list-item-content')
            print("此页面上共有", len(items), "条记录")

            # 遍历记录
            for item in items:
                ii = {}
                # 标题
                title = item.find_element_by_class_name('title').text
                ii['title'] = title

                # # 下载链接
                download_link = item.find_element_by_class_name('list-option-doctype').find_element_by_tag_name(
                    'a').get_attribute('href')
                ii['download_link'] = download_link

                # 文件名称
                filename = regex_filename.search(download_link).group(1)
                ii['file_name'] = filename

                # 文档名称
                # 压缩文件：https://download.schneider-electric.com/files?p_Archive_Name=APC_SY_696_EN.zip&p_enDocType=Firmware&p_Doc_Ref=APC_SY_696_EN
                # 单个文件：https://download.schneider-electric.com/files?p_enDocType=Firmware&p_File_Name=NBRK0750_Build_5.2.4.15.sedp&p_Doc_Ref=APC_SFNBZ_524_EN

                # 获取当前窗口句柄
                now_handle = driver.current_window_handle

                # 访问详情页
                detail_href = item.find_element_by_xpath('h5/a').get_attribute('href')
                ii['detail_page'] = detail_href
                driver.execute_script("window.open('" + detail_href + "');")
                handles = driver.window_handles
                driver.switch_to.window(handles[-1])
                time.sleep(5)

                # noinspection PyBroadException
                try:
                    driver.find_element_by_class_name('detail')
                except Exception:
                    print(title)
                else:
                    # 样本号
                    number = driver.find_element_by_xpath('//*[@id="preview-content"]/div[2]/div/ul/li[1]/p').text
                    ii['number'] = number
                    # 类型
                    tp = driver.find_element_by_xpath('//*[@id="preview-content"]/div[2]/div/ul/li[2]/p').text
                    ii['type'] = tp

                    # 语言
                    language = driver.find_element_by_xpath('//*[@id="preview-content"]/div[2]/div/ul/li[3]/p').text
                    ii['language'] = language

                    # 日期
                    date = driver.find_element_by_xpath('//*[@id="preview-content"]/div[2]/div/ul/li[4]/p').text
                    ii['date'] = datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')

                    # 版本
                    version = driver.find_element_by_xpath('//*[@id="preview-content"]/div[2]/div/ul/li[5]/p').text
                    ii['version'] = version

                    # 产品名称
                    product = driver.find_element_by_xpath('//*[@id="preview-content"]/div[4]/p/span/span').text
                    ii['product_name'] = product
                finally:
                    # 关闭当前标签页
                    driver.close()
                    # 返回原来的标签
                    driver.switch_to.window(now_handle)

                    list_items.append(ii)
                    # 写入文件
                    writer.writerow(ii)

            # 关闭当前标签
            driver.close()
            # 切回原来的标签
            driver.switch_to.window(handles[0])

    # 关闭浏览器
    driver.quit()
    # 返回列表
    print(list_items)
    return list_items


def write_json(file_name, data):
    with open(file_name, 'a', encoding='utf-8') as json_file:
        for d in data:
            # json_file.write(json.dumps(d, indent=2, ensure_ascii=False))
            json.dump(d, json_file, indent=2, ensure_ascii=False)


def write_csv(file_name, fieldnames, data):
    with open(file_name, 'a', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def write_mysql(data, table):
    # data = [{}, {}, ...]，转换为tuple的list
    t = []
    for d in data:
        t.append(tuple(d.values()))

    db = pymysql.connect(host='localhost', user='root', password='qwe123',
                         port=3306, db='spiders', unix_socket="/tmp/mysql.sock")
    cursor = db.cursor()

    keys = ','.join(data[0].keys())
    values = ','.join(['%s'] * len(data[0]))

    sql = 'INSERT INTO {table} ({keys}) VALUES ({values})'.format(table=table, keys=keys, values=values)

    # noinspection PyBroadException
    try:
        # 批量导入
        # if cursor.execute(sql, tuple(data.values())):
        if cursor.executemany(sql, t):
            print('Successful')
            db.commit()
    except Exception as e:
        print('Failed Reason: ', e)
        db.rollback()
    db.close()


def _progress(block_num, block_size, total_size):
    """
    回调函数
    @block_num: 已经下载的数据块
    @block_size: 数据块的大小
    @total_size: 远程文件的大小
    """
    per = float(block_num * block_size) / float(total_size) * 100.0
    if per > 100:
        per = 100
    sys.stdout.write('\r>> Downloading %.1f%%' % per)
    sys.stdout.flush()


def batch_download(df, table, directory, error_logs_path):
    # 拉动请求，模拟成浏览器去访问网站->跳过反爬虫机制
    # 添加headers
    user_agent = ('User-Agent',
                  'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36')

    headers = [user_agent]
    opener = request.build_opener()
    opener.addheaders = headers
    request.install_opener(opener)

    for d in df.itertuples():
        # 把目录和文件名合成一个路径
        filename = os.path.join(directory, table, '(' + str(getattr(d, 'number')) + ')' + getattr(d, 'file_name'))
        print('\nfile: ', filename)
        if not os.path.isfile(filename):
            auto_down(getattr(d, 'download_link'), filename, error_logs_path)
        else:
            with open(error_logs_path, 'a') as error_logs:
                error_logs.write(filename + ',' + getattr(d, 'download_link') + '\n')
        time.sleep(3)


def auto_down(url, filename, error_logs_path):
    # # 设置超时时间为30s
    # socket.setdefaulttimeout(30)
    # 解决下载不完全问题且避免陷入死循环
    try:
        request.urlretrieve(url, filename, reporthook=_progress)
    # except (urllib.error.ContentTooShortError, socket.timeout):
    except urllib.error.ContentTooShortError:
        count = 1
        while count <= 15:
            try:
                request.urlretrieve(url, filename, reporthook=_progress)
                break
            except urllib.error.ContentTooShortError:
                err_info = 'Reloading for %d time' % count if count == 1 else 'Reloading for %d times' % count
                print(err_info)
                count += 1
        if count > 15:
            print("Download failed!")
            # 下载异常写入文件
            with open(error_logs_path, 'a') as error_logs:
                error_logs.write(filename + ',' + url + '\n')
    except urllib.error.HTTPError:
        with open(error_logs_path, 'a') as error_logs:
            error_logs.write(filename + ',' + url + '\n')


# 爬取Schneider
def spider_for_schneider():
    # url = "https://www.schneider-electric.cn/zh/download/doc-group-type/4868253-%E8%BD%AF%E4%BB%B6/%E5%9B%BA%E4%BB%B6/?docType=1555893-%E5%9B%BA%E4%BB%B6-%E5%8F%91%E5%B8%83&language=zh_CN-%E4%B8%AD%E6%96%87&sortByField=Popularity&itemsPerPage=10"

    url = "https://www.schneider-electric.cn/zh/download/doc-group-type/4868253-%E8%BD%AF%E4%BB%B6/%E5%9B%BA%E4%BB%B6/?docType=1555893-%E5%9B%BA%E4%BB%B6-%E5%8F%91%E5%B8%83&langFilterDisabled=true&keyword=fireware"
    # item_list = spider_by_page(url)
    '''
    # 写入json
    write_json('schneider_json.json', item_list)
    
    # 写入csv
    fieldnames = ['title',  'download_link',   'detail_page','number','type','language','date', 'version', 'product_name','file_name']
    write_csv('schneider_csv.csv', fieldnames, item_list)

    # 写入mysql
    write_mysql(item_list, 'schneider')

    # 从json里面读取
    with open('schneider_json.json', 'r') as file:
        s = file.read()
        data = json.loads(s)
        print(data)
    '''

    df = pd.read_csv('schneider_csv.csv')
    print(df[df.title == 'ION8650 V409 Firmware V409'])
    # print(df.iloc[232:, :])

    download_path = 'C:\\Users\\lj\\Desktop'
    error_logs_filename = os.path.join(download_path, 'schneider_' + 'error_logs.txt')
    batch_download(df.iloc[498:, :], 'schneider', download_path, error_logs_filename)


# 主函数
if __name__ == '__main__':
    spider_for_schneider()
