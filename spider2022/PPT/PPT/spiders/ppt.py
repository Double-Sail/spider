import scrapy


class PptSpider(scrapy.Spider):
    name = "ppt"
    allowed_domains = ["www.baidu.com"]
    start_urls = ["http://www.baidu.com/"]

    def parse(self, response):
        pass
