import logging
import logging.config
import yaml
import importlib
from pathlib import Path
from typing import Dict, Any
from pyfiglet import Figlet

import sycu.libs.enums as enums_module
from sycu.libs.enums import create_grade_type_enum, create_course_type_enum


def read_config_file(file_path: str) -> Dict[str, Any]:
    """读取并解析YAML配置文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"文件 {file_path} 未找到。")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"解析 {file_path} 文件时出错: {e}")


def initialize_logger(config: Dict[str, Any]) -> logging.Logger:
    """初始化日志配置并返回logger实例"""
    logging.config.dictConfig(config["Logger"])
    return logging.getLogger("sycu")


def create_model_instance(
    model_name: str, configs: Dict[str, Any], logger: logging.Logger
):
    """创建策略实例"""
    module = importlib.import_module(f"sycu.course.{model_name}")
    module_class = getattr(module, model_name)
    return module_class(configs, logger=logger)


def main():

    # 读取配置文件
    config_path = Path("sycu_config.yaml")
    config_data = read_config_file(config_path)

    # 初始化日志
    logger = initialize_logger(config_data)

    # 从配置文件动态创建 GradeType 枚举
    common_config = config_data.get("common", {})
    grade_types = common_config.get("grade_types", ["23", "24", "25"])
    enums_module.GradeType = create_grade_type_enum(grade_types)

    # 从配置文件动态创建 CourseType 枚举
    course_types = common_config.get("course_types", {})
    if course_types:
        enums_module.CourseType = create_course_type_enum(course_types)

    f = Figlet(font="standard")
    logger.info(f"\n{f.renderText('sycu-exam')}")

    # 遍历 actived_course，根据每个课程的 actived_model 动态加载模型
    courses_config = config_data.get("couses", {})
    actived_courses = courses_config.get("actived_course", [])

    for course_name in actived_courses:
        course_config = courses_config.get(course_name, {})
        model_name = course_config.get("actived_model")

        logger.info(f"Begin... {'-'* 60}")
        if not model_name:
            logger.warning(f"课程 {course_name} 未配置 actived_model，跳过")
            continue

        logger.info(f"处理课程: {course_name}, 使用模型: {model_name} ")

        # 将当前课程名传入配置，供模型使用
        config_data["current_course"] = course_name
        model = create_model_instance(model_name, config_data, logger)
        model.start()


if __name__ == "__main__":
    main()
