import re
import scrapy
from ..items import PptItem
from ..log import Log

# 用于拼接url
url_montage = "https://www.1ppt.com"
log = Log.log


class PptSpider(scrapy.Spider):
    # 说明爬虫项目名字，用于后续启动爬虫
    name = "ppt"
    # 限制爬取域名，避免网页中的其他广告页面的干扰
    allowed_domains = ["www.1ppt.com"]
    # 给定起始链接（一般多级页面爬取，会直接注释掉，重写）
    start_urls = ["https://www.1ppt.com/xiazai/"]

    def parse(self, response, *args, **kwargs):
        """
        爬虫文件向引擎说明请求，然后传给调度器，经过中间件后，最后传入下载器，最后返回response，也就是该方法的入参
        后续再在这个方法里面对response进行处理
        """
        log.info("开始进行第一页面处理")
        li_list = response.xpath('//div[@class="col_nav clearfix"]/ul/li')
        # 列表中的第一个元素是“栏目分类”，只要分类名即可，这个元素舍弃掉
        # 避免过多访问，只爬取两个种类
        for li in li_list[1:3]:
            item = PptItem()
            # 获取分类名
            ppt_class_name = li.xpath('./a/text()').get()
            item['ppt_class_name'] = ppt_class_name
            # 获取分类链接，并传入调度器
            ppt_class_href = url_montage + li.xpath('./a/@href').get()
            # yield关键字，表示此段语句，允许再运行时暂停。这也是scrapy中的协程操作
            # meta这个属性的作用不仅可以用于在不同方法间进行数据传输（多级页面爬取必须），还可以定义代理
            yield scrapy.Request(url=ppt_class_href, meta={'meta1': item, 'ppt_class_href': ppt_class_href},
                                 callback=self.parse_second_page)
            log.info(f"已获取{ppt_class_name}")

    def parse_second_page(self, response):
        """
        二级页面有多页，提取每一页的url
        """
        li_list = response.xpath('//ul[@class="pages"]/li')

        # 此页面不需要更新item
        # 首页和尾页这两个值不需要。第一页的链接直接给的thisclass，所以li.xpath('./a/@href').get()拿不到值
        # 第一页的page_url直接给response.url即可
        # len_list = len(li_list) - 1
        # 只爬取两页
        for i in range(1, 3):
            page_url = response.meta['ppt_class_href']
            if i != 1:
                li = li_list[i]
                page_url = page_url + li.xpath('./a/@href').get()
                # 更新meta，就算不变也要更新，不然传不下去
            yield scrapy.Request(url=page_url, meta={'meta2': response.meta['meta1']},
                                 callback=self.parse_third_page,
                                 dont_filter=True)

    def parse_third_page(self, response):
        """
        三级页面提取ppt文件的名字和详细信息页面
        """
        # 接收上一个请求函数中传递过来的item对象
        # 上一级页面没有更新item，直接去第一级的
        meta2 = response.meta['meta2']
        li_list = response.xpath('//ul[@class="tplist"]/li')

        # 避免过多访问，只取当前页的第一个ppt文件
        for li in li_list[0:1]:
            # 每次传输需要重新建一个item对象，不然多个输入，后面会覆盖前一个数据
            # 这是一个坑，只要是循环，必须要重新申明对象，并且item中的上一级的数据也要重新赋值，再传给下一层
            item = PptItem()
            ppt_name = li.xpath('./h2/a/text()').get()
            item['ppt_name'] = ppt_name
            # 由于新建了一个item对象，ppt种类命名也需要更新，然后继续往下一级传
            item['ppt_class_name'] = meta2['ppt_class_name']
            ppt_info_url = url_montage + li.xpath('./h2/a/@href').get()

            # 将ppt详情页面放入调度器
            yield scrapy.Request(url=ppt_info_url, meta={'meta3': item}, callback=self.parse_forth_page)
            log.info(f"已获取{ppt_name}")

    def parse_forth_page(self, response):
        """
        需要提取ppt下载页
        由于数据进行了加密，下一级为解密，解密之后需要重新加载ppt下载页，所以meta中要存入当前下载页的链接
        """

        item = response.meta['meta3']
        enter_download_page = url_montage + response.xpath('//ul[@class="downurllist"]/li/a/@href').get()
        yield scrapy.Request(url=enter_download_page, meta={'meta4': item, 'enter_download_page': enter_download_page},
                             callback=self.parse_fifth_page)
        log.info(f"进入{item['ppt_name']}下载页面")

    def parse_fifth_page(self, response):
        """
        解密并传入调度器
        """
        # 直接读本地js代码也行，不用转python了
        # arg1 = re.search('arg1=\'[0-9A-Z]+\'', response.text).group().replace('arg1=', '').replace('\'', '')
        # with open('./get_acw_sc_v2.js', 'r', encoding='utf-8') as f:
        #     acw_sc_v2_js = f.read()
        # acw_sc__v2 = execjs.compile(acw_sc_v2_js).call('getAcwScV2', arg1)
        # true_cookie.update({"acw_sc__v2": acw_sc__v2})

        # 解密
        true_cookie = {}

        _seceret_key1 = re.search('arg1=\'[0-9A-Z]+\'', response.text).group().replace('arg1=', '').replace('\'', '')

        # 密钥2，是一个固定值
        _seceret_key2 = '3000176000856006061501533003690027800375'
        _new_cookie = hexXor(_seceret_key2, unsbox(_seceret_key1)).replace('0x', '')
        true_cookie.update({"acw_sc__v2": _new_cookie})

        item = response.meta["meta4"]
        enter_download_page = response.meta["enter_download_page"]
        # 在更新cookie之后，需要重新加载下载页面，也就是要重新进行请求。
        # 这个请求和重新加载前的页面唯一的区别就是cookie更新为解密之后，生成的cookie，但是url链接并没有发生变化
        # 而调度器有去重功能，去重仅仅基于sha1的加密算法生成指纹做判断的，而不是看两个请求整体是不是一样，这就导致更新后的请求进入调度器之后，会被过滤
        # 所以这一级页面的请求，需要将dont_filter设置成True
        yield scrapy.Request(url=enter_download_page, meta={'meta5': item}, callback=self.parse_sixth_page,
                             cookies=true_cookie, dont_filter=True)

    def parse_sixth_page(self, response):
        """
        提取的是具体的ppt下载链接
        """
        item = response.meta["meta5"]
        # 到了最后一页，item中的下载地址可以赋值了
        item['ppt_download_url'] = response.xpath("//ul[@class='downloadlist']/li[1]/a/@href").get()

        yield item


def hexXor(_seceret_key1, _seceret_key):
    """
    解密程序2
    :param _seceret_key1: 密钥1
    :param _seceret_key: 密钥2
    :return: 更新完毕的cookie
    """
    _processed_seceret_str = ''
    for i in range(0, min(len(_seceret_key1), len(_seceret_key)), 2):
        _a = int(_seceret_key1[i:i + 2], 16)
        _b = int(_seceret_key[i:i + 2], 16)
        # 转换为16进制字符串
        _c = hex(_a ^ _b)[2:]
        if len(_c) == 1:
            _c = '0' + _c
        _processed_seceret_str += _c
    return _processed_seceret_str


def unsbox(seceret_key):
    """
    解密程序1
    :param seceret_key: response中，第一行的arg1
    :return: 解密后的密钥，传入第二个解密程序
    """
    _seceret_list = [15, 35, 29, 24, 33, 16, 1, 38, 10, 9, 19, 31, 40, 27, 22, 23, 25, 13, 6, 11, 39, 18, 20, 8, 14, 21,
                     32, 26, 2, 30, 7, 4, 17, 5, 3, 28, 34, 37, 12, 36]
    _processed_seceret_list0dc = [''] * len(_seceret_list)
    _processed_seceret_str = ''
    for i in range(len(seceret_key)):
        _seceret_key_element = seceret_key[i]
        for j in range(len(_seceret_list)):
            if _seceret_list[j] == i + 1:
                _processed_seceret_list0dc[j] = _seceret_key_element
    _processed_seceret_str = ''.join(_processed_seceret_list0dc)
    return _processed_seceret_str

# js中是直接更新cookie，此段代码无需执行，解析出新的cookie之后，更新cookie重新加载页面就行
# def setCookie(name, value):
#     expiredate = datetime.datetime.now() + datetime.timedelta(hours=1)
#     cookie_str = f"{name}={value};expires={expiredate.strftime('%a, %d %b %Y %H:%M:%S GMT')};max-age=3600;path=/"
#     return cookie_str
