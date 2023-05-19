from scrapy import cmdline

# 这样写可以直接输出为csv文件
cmdline.execute('scrapy crawl ppt -o ppt.csv'.split())
