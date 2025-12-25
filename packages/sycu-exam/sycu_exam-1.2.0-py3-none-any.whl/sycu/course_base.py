import logging

from abc import abstractmethod
from typing import Dict, Any


class CourseBase:
    def __init__(self, configs: Dict[str, Any], logger: logging.Logger):
        self.configs = configs
        self.logger = logger

    @abstractmethod
    def start(self):
        raise NotImplementedError("必须在子类中实现start方法")
