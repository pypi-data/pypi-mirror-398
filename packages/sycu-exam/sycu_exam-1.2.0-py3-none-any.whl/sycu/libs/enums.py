from enum import Enum
APP_NAME = "sycu_exam"


class CourseTypeBase:
    """CourseType 的属性容器"""
    def __init__(self, value: str, score: int, shiyan_times: int, xiaozu_times: int, zuoye_times: int, jieke_type: str):
        self.value = value
        self.score = score
        self.shiyan_times = shiyan_times
        self.xiaozu_times = xiaozu_times
        self.zuoye_times = zuoye_times
        self.jieke_type = jieke_type


def create_course_type_enum(course_types: dict):
    """从配置字典动态创建 CourseType 枚举

    Args:
        course_types: {"JAVA": ["java", 3, 1, 1, 3, "exam"], ...}
    """
    members = {}
    for name, params in course_types.items():
        members[name] = CourseTypeBase(*params)

    # 创建枚举类
    course_enum = Enum("CourseType", {k: v.value for k, v in members.items()})

    # 为每个枚举成员添加属性
    for member in course_enum:
        base = members[member.name]
        member.score = base.score
        member.shiyan_times = base.shiyan_times
        member.xiaozu_times = base.xiaozu_times
        member.zuoye_times = base.zuoye_times
        member.jieke_type = base.jieke_type

    return course_enum


# 默认值，会在 main.py 中被配置文件的值覆盖
_default_course_types = {
    "JAVA": ["java", 3, 1, 1, 3, "exam"],
    "ML": ["ml", 2, 1, 0, 0, "paper"],
    "C_PLUS": ["c++", 2, 0, 1, 3, "paper"],
    "NETWORK": ["network", 2, 0, 1, 3, "exam"],
    "LINUX": ["linux", 2, 0, 1, 3, "exam"],
    "WEB": ["web", 3, 1, 1, 3, "paper"],
    "MACHINE": ["machine", 2, 0, 1, 3, "paper"],
}
CourseType = create_course_type_enum(_default_course_types)


class JieKeType(Enum):
    EXAM = "exam"
    PAPER = "paper"

def create_grade_type_enum(grade_types: list):
    """从配置列表动态创建 GradeType 枚举"""
    members = {f"SK{gt}": gt for gt in grade_types}
    return Enum("GradeType", members)


# 默认值，会在 main.py 中被配置文件的值覆盖
GradeType = create_grade_type_enum(["23", "24", "25"])


class ClazzType(Enum):
    """班级类型枚举"""
    C1 = "1"  # 一班
    C2 = "2"  # 二班
    C3 = "3"  # 三班
    C4 = "4"  # 四班  
    C5 = "5"  # 五班
