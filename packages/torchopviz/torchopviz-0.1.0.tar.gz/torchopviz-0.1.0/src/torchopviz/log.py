import inspect
import sys
from datetime import datetime
from enum import Enum
from typing import Optional

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class TorchOpVizLogger:
    """TorchOpViz 专用日志器"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level
        self._level_num = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50
        }
    
    def _log(self, level: LogLevel, msg: str, frame_depth: int = 2):
        """内部日志方法"""
        if self._level_num[level] < self._level_num[self.level]:
            return
        
        # 获取调用者信息
        frame = inspect.currentframe()
        for _ in range(frame_depth):
            frame = frame.f_back if frame else None
        
        filename = "unknown"
        lineno = "??"
        if frame:
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
        
        # 只显示文件名，不显示完整路径
        filename_short = filename.split('/')[-1] if '/' in filename else filename
        filename_short = filename_short.split('\\')[-1] if '\\' in filename_short else filename_short
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 彩色输出
        color_map = {
            LogLevel.DEBUG: "\033[36m",     # 青色
            LogLevel.INFO: "\033[32m",      # 绿色
            LogLevel.WARNING: "\033[33m",   # 黄色
            LogLevel.ERROR: "\033[31m",     # 红色
            LogLevel.CRITICAL: "\033[41m",  # 红底
        }
        reset = "\033[0m"
        
        log_msg = f"[torchopviz] {color_map.get(level, '')}{level.value}{reset} [{timestamp}] {filename_short}:{lineno} - {msg}"
        print(log_msg)
    
    def debug(self, msg: str):
        self._log(LogLevel.DEBUG, msg)
    
    def info(self, msg: str):
        self._log(LogLevel.INFO, msg)
    
    def warning(self, msg: str):
        self._log(LogLevel.WARNING, msg)
    
    def error(self, msg: str):
        self._log(LogLevel.ERROR, msg)
    
    def critical(self, msg: str):
        self._log(LogLevel.CRITICAL, msg)
    
    def set_level(self, level: LogLevel):
        """设置日志级别"""
        self.level = level

# 创建全局日志器实例
logger = TorchOpVizLogger()

# 使用示例
if __name__ == "__main__":
    logger.info("初始化 TorchOpViz")
    logger.debug("加载配置文件")
    logger.warning("未找到缓存文件")
    logger.error("模型加载失败")
    logger.critical("致命错误：内存溢出")