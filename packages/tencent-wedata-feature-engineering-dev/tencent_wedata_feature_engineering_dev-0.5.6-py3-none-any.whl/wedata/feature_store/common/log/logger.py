import logging
import sys


class LoggerSingleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        self.logger = logging.getLogger("wedata-feature-engineering")
        self.logger.setLevel(logging.INFO)

        # 清除已有的handler，避免重复添加
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 创建formatter，包含时间、文件名和行号
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建handler并输出到stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
        # 防止消息传播到父级logger
        self.logger.propagate = False
    
    def get_logger(self, level=logging.INFO):
        self.logger.setLevel(level)
        return self.logger


def get_logger(level=logging.INFO):
    """获取单例logger实例"""
    return LoggerSingleton().get_logger(level)