import logging
from typing import Dict, Any

from sycu.course_base import CourseBase
from sycu.libs.enums import GradeType,ClazzType,CourseType
from sycu.libs.GradeTool import GradeTool


class Three(CourseBase):
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        super().__init__(config, logger)
        self.logger.info("Three初始化完成")
        self.course_config = config["couses"]
        self.current_course = config.get("current_course")

    def start(self):
        self.logger.info("Three开始运行")

        if not self.current_course:
            self.logger.warning("未指定 current_course，跳过")
            return

        course_type = CourseType[self.current_course.upper()]
        course_config = self.course_config.get(self.current_course, {})
        grades = course_config.get("GradeType", [])
        clazzes = course_config.get("ClazzType", [])

        for grd in grades:
            grd_type = GradeType[grd.upper()]
            for cls in clazzes:
                cls_type = ClazzType[cls.upper()]
                GradeTool(grd=grd_type, cls=cls_type, course=course_type, logger=self.logger).do()

        self.logger.info("Three运行结束")
