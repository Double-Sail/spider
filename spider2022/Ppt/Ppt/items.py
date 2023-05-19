"""
1.用来定义索要获取数据的形式，即传入管道中的数据形式，可以理解为mysql中的字段名字
2.本项目对于下载的ppt，需要在当前主目录下建一个pptfile文件夹，然后在此文件夹内部根据不同的ppt分类建立子文件夹，然后再在里面存放具体的ppt文件
3.为了将pipeline模块的功能也展示，还要输出下载过的ppt的类别，名字，和下载链接。输入到csv和mysql
4.所以传给管道的就至少是三个参数，ppt种类名字，ppt文件名字，ppt文件下载链接
"""
import scrapy


class PptItem(scrapy.Item):
    """
    相当于定义了一个字典，字典的key就是以下变量的名字，类似于mysql的字段
    scrapy.Field()表示字典的value先空着，然后根据后续爬取的数据，填入其中
    """
    ppt_class_name = scrapy.Field()
    ppt_name = scrapy.Field()
    ppt_download_url = scrapy.Field()
    pass

