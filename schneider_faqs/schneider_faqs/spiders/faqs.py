from functools import reduce

import scrapy
from schneider_faqs.items import *

import re


class FaqsSpider(scrapy.Spider):
    name = 'faqs'
    allowed_domains = ['www.se.com']
    base_url = 'https://www.se.com/ww/en/faqs/FA{id}/'  # https://www.se.com/ww/en/faqs/FA239112/

    def start_requests(self):
        # 浏览器用户代理
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        }

        # 生成六位数字字符串
        for i in range(400000, 600000):
            num = str(i)  # 数字转化为字符串
            six_num = num.zfill(6)  # 字符串右对齐补0
            yield scrapy.Request(url=self.base_url.format(id=six_num), headers=headers, callback=self.parse)

        # ids = [239112, 198605, 198604, 198600, 198567, 198919, 195904, 196713, 178883, 163608, 176117, 198709]
        # for i in ids:
        #     url = self.base_url.format(id=i)
        #     yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        # title
        title = response.xpath(
            '//*[@id="detailPageContentContainer"]/div[@class="detailColumn Column"]/h1['
            '@class="im-content-title"]/text()')
        # file
        file_links = response.xpath(
            '//*[@id="detailPageContentContainer"]/div[@class="detailColumn Column"]//a/@href').extract()
        items_list = []
        for link in file_links:
            item = SchneiderFaqsItem()
            item['detail_page'] = response.url
            item['title'] = title.extract_first()

            file_name = link.split('/')[-1]  # re.search(r'/([.\w]+)$', url).group(1)
            # 按后缀名过滤
            if len(re.findall(r'\.(pdf|ppt|txt|doc|xls|mov|bmp|jpg|png|htm|com|sql|mp4)[\.]?', file_name, flags=re.IGNORECASE)):
                continue

            # 正则提取文件名
            regex_filename = re.search(r'Name=([\s\S]*?)&', file_name)
            if regex_filename:
                file_name = regex_filename.group(1)

            item['file_name'] = file_name.replace('%20', ' ')

            # 过滤无效链接
            if link.startswith('index?page'):
                continue
            if link.startswith('/'):  # re.match(r'/', link)
                link = response.urljoin(link)  # 'https://www.se.com'+link

            item['download_link'] = [link]
            items_list.append(item)

        # list[dict]去重
        items = reduce(lambda x, y: x if y in x else x + [y], [[], ] + items_list)
        for i in items:
            yield i
