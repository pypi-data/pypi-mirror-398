# logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import inspect
from dataset_down.config.constants import NAME


class CallerAwareFormatter(logging.Formatter):
    """自定义格式化器，能正确显示调用日志的原始文件和行号"""
    
    def format(self, record):
        # 保存原始的filename和lineno
        original_filename = record.filename
        original_lineno = record.lineno
        
        filename,lineno = self._get_caller_info()
        record.filename = filename
        record.lineno = lineno

        # 使用更新后的记录格式化
        result = super().format(record)
        
        # 恢复原始值（如果需要）
        record.filename = original_filename
        record.lineno = original_lineno
        
        return result
    
    
    def _get_caller_info(self):
        """
        获取调用者信息
        """
        frame = inspect.currentframe()
        try:
            # 遍历调用栈，找到第一个不是日志相关模块的帧
            while frame:
                filename = os.path.basename(frame.f_code.co_filename)
                module_path = frame.f_code.co_filename
                # 跳过logging模块相关的所有文件和logger.py自身的调用
                if (not module_path.endswith('logging\\__init__.py') and 
                    not module_path.endswith('logging\\handlers.py') and
                    not module_path.endswith('logging\\formatter.py') and
                    filename != 'logger.py'):
                    return filename,frame.f_lineno
                frame = frame.f_back
            # 如果没找到合适的调用者，返回默认值
            return 'unknown',0
        except Exception:
            # 异常情况下返回默认值，避免影响日志记录
            return 'unknown',0
        finally:
            del frame  # 避免循环引用


class Logger:
    """
    日志管理类，提供统一的日志记录功能
    """
    
    _instances = {}
    
    def __new__(cls,name=NAME,log_dir='logs', level=logging.INFO):
        if name not in cls._instances:
            instance = super(Logger,cls).__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]

    def __init__(self, name=NAME, log_dir='logs', level=logging.INFO):
        """
        初始化日志器
        
        Args:
            name (str): 日志器名称
            log_dir (str): 日志文件存储目录
            level (int): 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers(log_dir, level)

    def _setup_handlers(self, log_dir, level):
        """
        设置日志处理器
        
        Args:
            log_dir (str): 日志目录
            level (int): 日志级别
        """
        # 创建自定义格式器
        formatter = CallerAwareFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - [%(thread)d] - %(message)s'
        )

        # 文件处理器（带轮转）
        log_file = os.path.join(log_dir, f'{NAME}_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=0,
            backupCount=5,
            encoding='utf-8',
            delay=True
        )
    
        #from logging.handlers import TimedRotatingFileHandler

        #file_handler = TimedRotatingFileHandler(
        #    log_file,
        #    when="midnight",
        #    interval=1,
        #    backupCount=7,
        #    encoding='utf-8'
        #)
        
        
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message):
        """记录一般信息"""
        self.logger.info(message)

    def warning(self, message):
        """记录警告信息"""
        self.logger.warning(message)

    def error(self, message):
        """记录错误信息"""
        self.logger.error(message)

    def critical(self, message):
        """记录严重错误信息"""
        self.logger.critical(message)


# 创建全局日志实例
app_logger = Logger()


# 便捷函数
def get_logger(name=None):
    """
    获取日志器实例
    
    Args:
        name (str): 日志器名称
        
    Returns:
        Logger: 日志器实例
    """
    if name:
        return Logger(name)
    return app_logger


if __name__ == '__main__':
    # 测试日志记录功能
    logger = get_logger()
    logger.debug('This is a debug message.')
    logger.info('This is an info message.')
    logger.warning('This is a warning message.')
    logger.error('This is an error message.')
    logger.critical('This is a critical message.')