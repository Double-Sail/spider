# scrapy针对文件类爬取，设置了不同的包，有文件、图片、视频等。
from scrapy.pipelines.files import FilesPipeline
import scrapy

class PptPipeline:
    def process_item(self, item, spider):
        return item
