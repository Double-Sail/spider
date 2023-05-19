import logging


class Log:
    log = logging.getLogger()
    log.setLevel("INFO")
    # 创建控制台Handler并设置日志级别为DEBUG
    console_handler = logging.StreamHandler()
    console_handler.setLevel("INFO")

    # 创建Formatter并将其添加到Handler中
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # 将Handler添加到logger中
    log.addHandler(console_handler)

    def __init__(self):
        self.log = Log
