import sys
import os

from pathlib import Path

from datetime import datetime
from loguru import logger
from platformdirs import user_log_path
from .enums import APP_NAME


logPath = Path(
    os.getenv("SYCU_LOG_DIR")
    or user_log_path(
        APP_NAME,
        appauthor=False,
        ensure_exists=True,
    )
)


class Logger:
    def __init__(self, log_name: str = "sycu-exam", log_path: Path = None):

        _file_name = log_path.joinpath(f"{log_name}.log").resolve()
        self.logger = logger  # 初始化一个logger
        self.logger.remove()  # 清空所有设置
        # 添加控制台输出的格式,sys.stdout为输出到屏幕
        self.logger.add(
            sys.stdout,
            format="<green>{time:YYYYMMDD HH:mm:ss}</green> | "  # 颜色>时间
            "{process.name} | "  # 进程名
            "{thread.name} | "  # 进程名
            "<cyan>{module}</cyan>.<cyan>{function}</cyan>"  # 模块名.方法名
            ":<cyan>{line}</cyan> | "  # 行号
            "<level>{level}</level>: "  # 等级
            "<level>{message}</level>",  # 日志内容
        )
        # 输出到文件
        rq = datetime.now().strftime("%Y%m%d")
        # file_name = log_path + log_name + "_" + rq + ".log"  # 文件名称
        self.logger.add(
            _file_name,
            level="DEBUG",
            format="{time:YYYYMMDD HH:mm:ss} - "  # 时间
            "{process.name} | "  # 进程名
            "{thread.name} | "  # 进程名
            "{module}.{function}:{line} - {level} -{message}",  # 模块名.方法名:行号
            # rotation="50 MB",
            rotation="1 day",
            compression="tar.gz",
        )

    def get_log(self):
        return self.logger


logger = Logger(log_path=logPath).get_log()
