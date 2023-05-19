"""
scrapy框架中的管道文件，负责将爬取的数据持久化存储
管道是一节拼一节的，可以在配置文件中配置每个管道的优先级
比如需要存一个csv，在存入mysql，在存入mongdb。则需要三节管道

scrapy中自己嵌入了csv文件存储模块，如果没有特殊要求，直接存csv是最方便的
"""
import pymysql
# scrapy针对文件类爬取，设置了不同的包，有文件、图片、视频等。
from scrapy.pipelines.files import FilesPipeline
import scrapy
import os
from .settings import *
from .log import Log

log = Log.log


class PptFilePipeline(FilesPipeline):
    """
    本项目爬的是文件，所以pipeline需要继承FilesPipeline，并重写get_media_requests
    """

    def get_media_requests(self, item, spider):
        # 将文件下载链接交给调度器。此方法的item，就是ppt.py文件中的meta最后传进来的
        yield scrapy.Request(url=item['ppt_download_url'], meta={'item': item})
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        item = request.meta['item']
        file_name = '{}/{}{}'.format(
            item['ppt_class_name'],
            item['ppt_name'],
            # 这里是仿造file里面的源码，用splitext方法，将文件的后缀名也提取出来，拼接进去文件名
            # 有些压缩包是zip，有些是rar。这么写，无论怎么变，都会拼接进入文件名中
            os.path.splitext(item['ppt_download_url'])[1]
        )
        return file_name


# class PptCsvPipeline:
#     def process_item(self, item):
#         return item


class PptMysqlPipeline(object):
    """
    把ppt的类别，名字，url输入MySQL
    在setting中定义链接，避免每次输入数据都要链接数据库
    """

    def open_spider(self, spider):
        """
        数据传输时，只执行一次，一般用于链接数据库，与开启游标
        """
        self.db = pymysql.Connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PWD, database=MYSQL_DB)
        self.cursor = self.db.cursor()
        log.info("mysql数据库已连接")
        pass

    def process_item(self, item,spider):
        pptInfo = [item['ppt_class_name'], item['ppt_name'], item['ppt_download_url']]
        self.cursor.execute('insert into pptinfo values (%s,%s,%s)', pptInfo)
        self.db.commit()
        return item

    def close_spider(self, spider):
        """
        只在所有数据传输结束后执行，用于关闭数据库和游标
        """
        self.cursor.close()
        self.db.close()
        log.info("mysql数据传输完成")
