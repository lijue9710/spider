# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import csv
import os
from urllib.parse import urlparse

import scrapy
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter


class CsvWriterPipeline:
    def __init__(self):
        store_file = os.path.dirname(__file__) + '/faqs2.csv'
        self.file = open(store_file, 'a', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)

    def process_item(self, item, spider):
        if item['file_name']:
            self.writer.writerow((item['file_name'], item['download_link'][0], item['title'], item['detail_page']))
        return item

    def close_spider(self, spider):
        self.file.close()


class SchneiderFilesPipeline(FilesPipeline):

    def file_path(self, request=None, response=None, info=None, *, item):
        return item['file_name']
        # return 'files/' + os.path.basename(urlparse(request.url).path)

    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        # for file_url in adapter['download_link']:
        #     yield scrapy.Request(file_url)
        url = adapter['download_link'][0]
        yield scrapy.Request(url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        # adapter = ItemAdapter(item)
        # adapter['file_paths'] = file_paths
        print(file_paths)

        return item
