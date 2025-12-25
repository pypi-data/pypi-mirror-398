import logging
import csv
import random
from pathlib import Path
from datetime import datetime

from sycu.libs.time_tools import format_timestamp
from sycu.libs.enums import CourseType,JieKeType,ClazzType,GradeType

class GradeTool:
    def __init__(self, course:CourseType, cls:str=ClazzType.C1, grd:str=GradeType.SK23, logger: logging.Logger=None) :
        """_summary_

        Args:
            course (CourseType): _description_
            cls (str, optional): _description_. Defaults to "1".  class No.
            grd (str, optional): _description_. Defaults to "23".
        """
        self.course  = course
        self.course_name = course.value
        self.sx_times = course.shiyan_times
        self.xz_times = course.xiaozu_times
        self.wk_times = course.zuoye_times
        self.cls =cls
        self.grd =grd
        self.jieke_type = course.jieke_type
        self.logger = logger

    
    def _check_file(self,file:Path)->None:
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
        
    def cent(self,low:int, high:int) -> int:
        cent = random.randint(low, high)
        return cent

    def jieke_lunwen_fun(self,row) -> list :
        jieke = 0
        cent1_1 = 5
        cent1_2 = 5
        if row[2] in ["A"]:
            cent2_1 = 10
            cent2_2 = self.cent(8, 9)
            cent2_3 = self.cent(8, 9)
            cent2_4 = self.cent(8, 9)

            cent3_1 = 5
            cent3_2 = 5
            cent3_3 = self.cent(3, 4)

            cent4_1 = 13
            cent5_1 = self.cent(8, 9)
            cent6_1 = 5
            cent6_2 = 5
        elif row[2] in ["A-"]:
            cent2_1 = self.cent(8, 9)
            cent2_2 = self.cent(8, 9)
            cent2_3 = self.cent(8, 9)
            cent2_4 = self.cent(7, 8)

            cent3_1 = 5
            cent3_2 = 5
            cent3_3 = 4

            cent4_1 = 12
            cent5_1 = self.cent(8, 9)
            cent6_1 = 5
            cent6_2 = 5
        elif row[2] in ["B+"]:
            cent2_1 = self.cent(7, 8)
            cent2_2 = self.cent(7, 8)
            cent2_3 = self.cent(7, 8)
            cent2_4 = self.cent(7, 8)

            cent3_1 = 5
            cent3_2 = 5
            cent3_3 = 4

            cent4_1 = 11
            cent5_1 = self.cent(8, 9)
            cent6_1 = 5
            cent6_2 = 5
        elif row[2] in ["B"]:
            cent2_1 = self.cent(6, 7)
            cent2_2 = self.cent(6, 7)
            cent2_3 = self.cent(7, 8)
            cent2_4 = self.cent(7, 8)

            cent3_1 = 5
            cent3_2 = 4
            cent3_3 = 5

            cent4_1 = 9
            cent5_1 = self.cent(8, 9)
            cent6_1 = 5
            cent6_2 = 5
        elif row[2] in ["B-"]:
            cent2_1 = self.cent(6, 7)
            cent2_2 = self.cent(6, 7)
            cent2_3 = self.cent(6, 7)
            cent2_4 = self.cent(6, 7)

            cent3_1 = 5
            cent3_2 = 4
            cent3_3 = 4

            cent4_1 = 8
            cent5_1 = self.cent(7, 8)
            cent6_1 = 4
            cent6_2 = 4
        elif row[2] in ["C+"]:
            cent2_1 = self.cent(7, 8)
            cent2_2 = self.cent(6, 7)
            cent2_3 = self.cent(6, 7)
            cent2_4 = self.cent(3, 4)

            cent3_1 = 5
            cent3_2 = 4
            cent3_3 = 4

            cent4_1 = 7
            cent5_1 = self.cent(6, 7)
            cent6_1 = 4
            cent6_2 = 4
        elif row[2] in ["C"]:
            cent2_1 = self.cent(7, 8)
            cent2_2 = self.cent(6, 7)
            cent2_3 = self.cent(6, 7)
            cent2_4 = self.cent(4, 5)

            cent3_1 = 3
            cent3_2 = 3
            cent3_3 = 3

            cent4_1 = 7
            cent5_1 = self.cent(6, 7)
            cent6_1 = 3
            cent6_2 = 3
        else:
            cent2_1 = self.cent(6, 7)
            cent2_2 = self.cent(6, 7)
            cent2_3 = self.cent(6, 7)
            cent2_4 = 0

            cent3_1 = 3
            cent3_2 = 3
            cent3_3 = 3

            cent4_1 = 5
            cent5_1 = self.cent(5, 6)
            cent6_1 = 3
            cent6_2 = 3

        jieke = (
            cent1_1
            + cent1_2
            + cent2_1
            + cent2_2
            + cent2_3
            + cent2_4
            + cent3_1
            + cent3_2
            + cent3_3
            + cent4_1
            + cent5_1
            + cent6_1
            + cent6_2
        )

        cents = []
        cents.append(row[0])
        cents.append(row[1])
        cents.append(row[2])
        cents.append(row[3])
        cents.append(jieke)
        cents.append(cent1_1)
        cents.append(cent1_2)
        cents.append(cent2_1)
        cents.append(cent2_2)
        cents.append(cent2_3)
        cents.append(cent2_4)
        cents.append(cent3_1)
        cents.append(cent3_2)
        cents.append(cent3_3)
        cents.append(cent4_1)
        cents.append(cent5_1)
        cents.append(cent6_1)
        cents.append(cent6_2)

        return cents

    def jieke_exam_fun(self,row) -> list:
        jieke = 0
        cent1_1 = 4
        cent1_2 = 4
        cent1_3 = 12
        cent1_4 = 4
           
        cent3_1 = 2
        cent3_2 = 4
        cent3_3 = 10
        cent3_4 = 4
        
        match row[2]:
            case "A":
                cent2_1 = 4
                cent2_2 = 12
                cent2_3 = 4

                cent4_1 = 8
                cent4_2 = self.cent(5, 6)
                cent4_3 = 8

                cent5_1 = 4
                cent5_2 = 0
                cent5_3 = 0
            case "A-":
                cent2_1 = 4
                cent2_2 = 12
                cent2_3 = 4

                cent4_1 = 8
                cent4_2 = self.cent(5, 6)
                cent4_3 = 6

                cent5_1 = 4
                cent5_2 = 0
                cent5_3 = 0
            case "B+":
                cent2_1 = 4
                cent2_2 = 12
                cent2_3 = 4

                cent4_1 = 7
                cent4_2 = self.cent(5, 6)
                cent4_3 = 8

                cent5_1 = 4
                cent5_2 = 0
                cent5_3 = 0
            case "B":
                cent2_1 = 4
                cent2_2 = 8
                cent2_3 = 4

                cent4_1 = 6
                cent4_2 = self.cent(4, 6)
                cent4_3 = 4

                cent5_1 = 0
                cent5_2 = 0
                cent5_3 = 0
            case "B-":
                cent2_1 = 4
                cent2_2 = 8
                cent2_3 = 4

                cent4_1 = 6
                cent4_2 = self.cent(4, 5)
                cent4_3 = 2

                cent5_1 = 0
                cent5_2 = 0
                cent5_3 = 0
            case "C+":
                cent2_1 = 4
                cent2_2 = 8
                cent2_3 = 4

                cent4_1 = 6
                cent4_2 = self.cent(4, 6)
                cent4_3 = 0

                cent5_1 = 0
                cent5_2 = 0
                cent5_3 = 0
            case "C":
                cent2_1 = 4
                cent2_2 = 8
                cent2_3 = 4

                cent4_1 = 0
                cent4_2 = self.cent(2, 4)
                cent4_3 = 0

                cent5_1 = 0
                cent5_2 = 0
                cent5_3 = 0
            case _:
                cent2_1 = 4
                cent2_2 = 4
                cent2_3 = 2

                cent4_1 = 0
                cent4_2 = 0
                cent4_3 = 0

                cent5_1 = 0
                cent5_2 = 0
                cent5_3 = 0        
        
      


        jieke = (
            cent1_1
            + cent1_2
            + cent1_3
            + cent1_4
            + cent2_1
            + cent2_2
            + cent2_3
            + cent3_1
            + cent3_2
            + cent3_3
            + cent3_4
            + cent4_1
            + cent4_2
            + cent4_3
            + cent5_1
            + cent5_2
            + cent5_3
        )
        # if self.course is CourseType.NETWORK:
        #     jieke +=   cent1_5 + cent1_6  + cent3_5  + cent3_6
    
 
        cents = []
        cents.append(row[0])
        cents.append(row[1])
        cents.append(row[2])
        cents.append(row[3])
        cents.append(jieke)
        cents.append(cent1_1)
        cents.append(cent1_2)
        cents.append(cent1_3)
        cents.append(cent1_4)
        cents.append(cent2_1)
        cents.append(cent2_2)
        cents.append(cent2_3)
        cents.append(cent3_1)
        cents.append(cent3_2)
        cents.append(cent3_3)
        cents.append(cent3_4)
        cents.append(cent4_1)
        cents.append(cent4_2)
        cents.append(cent4_3)
        cents.append(cent5_1)
        cents.append(cent5_2)
        cents.append(cent5_3)
        return cents

    def xiaozu_fun(self,row) -> list:
        # 程序代码编写及附加信息（55分）
        xiaozu = 0
        cent1_1 = 10
        cent2_1 = 10
        # 小组给分
        if row[3] in ["A"]:
            cent3_1 = 10
            cent4_1 = 10
            cent5_1 = 26
        elif row[3] in ["B"]:
            cent3_1 = 8
            cent4_1 = 8
            cent5_1 = 23
        else:
            cent3_1 = 7
            cent4_1 = 7
            cent5_1 = 20

        if row[2] in ["A"]:
            cent6_1 = self.cent(9, 10)
            cent7_1 = self.cent(9, 10)
            cent8_1 = self.cent(8, 9)

        elif row[2] in ["B+"]:
            cent6_1 = self.cent(8, 9)
            cent7_1 = self.cent(8, 9)
            cent8_1 = self.cent(8, 9)
        elif row[2] in ["B"]:
            cent6_1 = self.cent(6, 8)
            cent7_1 = self.cent(6, 8)
            cent8_1 = self.cent(6, 8)
        elif row[2] in ["C+"]:
            cent6_1 = self.cent(5, 7)
            cent7_1 = self.cent(5, 7)
            cent8_1 = self.cent(5, 7)
        elif row[2] in ["C"]:
            cent6_1 = self.cent(4, 5)
            cent7_1 = self.cent(4, 5)
            cent8_1 = self.cent(4, 5)
        else:
            cent6_1 = 1
            cent7_1 = 1
            cent8_1 = 1

        xiaozu = (
            cent1_1 + cent2_1 + cent3_1 + cent4_1 + cent5_1 + cent6_1 + cent7_1 + cent8_1
        )
        cents = []
        cents.append(row[0])
        cents.append(row[1])
        cents.append(row[2])
        cents.append(row[3])
        cents.append(xiaozu)
        cents.append(cent1_1)
        cents.append(cent2_1)
        cents.append(cent3_1)
        cents.append(cent4_1)
        cents.append(cent5_1)
        cents.append(cent6_1)
        cents.append(cent7_1)
        cents.append(cent8_1)
        return cents

    def shixu_fun(self,row) -> list:
        shixun = 0
        cent1_1 = 10
        # cent1_2 = 5
        if row[2] in ["A"]:
            cent2_1 = 12
            cent2_2 = 15
            cent2_3 = 10
            cent2_4 = 15

            cent3_1 = 10
            cent4_1 = self.cent(12, 14)
            cent5_1 = 9
        elif row[2] in ["B+"]:
            cent2_1 = 12
            cent2_2 = 10
            cent2_3 = 10
            cent2_4 = self.cent(12, 14)

            cent3_1 = 10
            cent4_1 = self.cent(12, 14)
            cent5_1 = 9
        elif row[2] in ["B"]:
            cent2_1 = 9
            cent2_2 = 10
            cent2_3 = 10
            cent2_4 = self.cent(12, 14)
            
            cent3_1 = 10
            cent4_1 = self.cent(12, 14)
            cent5_1 = 8
        elif row[2] in ["C+"]:
            cent2_1 = 9
            cent2_2 = 7
            cent2_3 = 10
            cent2_4 = self.cent(10, 12)

            cent3_1 = 8
            cent4_1 = self.cent(12, 14)
            cent5_1 = 7
        elif row[2] in ["C"]:
            cent2_1 = 9
            cent2_2 = 5
            cent2_3 = 5
            cent2_4 = self.cent(10, 12)

            cent3_1 = 8
            cent4_1 = self.cent(10, 13)
            cent5_1 = 6
        else:
            cent2_1 = 6
            cent2_2 = 5
            cent2_3 = 0
            cent2_4 = self.cent(10, 12)

            cent3_1 = 10
            cent4_1 = self.cent(8, 10)
            cent5_1 = 6

        shixun = (
            cent1_1
            # + cent1_2
            + cent2_1
            + cent2_2
            + cent2_3
            + cent2_4
            # + cent2_5
            # + cent2_6
            + cent3_1
            + cent4_1
            + cent5_1
        )
        cents = []
        cents.append(row[0])
        cents.append(row[1])
        cents.append(row[2])
        cents.append(row[3])
        cents.append(shixun)
        cents.append(cent1_1)

        cents.append(cent2_1)
        cents.append(cent2_2)
        cents.append(cent2_3)
        cents.append(cent2_4)

        cents.append(cent3_1)
        cents.append(cent4_1)
        cents.append(cent5_1)
   

        return cents

    def jieduan_fun(self,row) -> list:
        jieduan = 0
        cent1_1 = 5
        cent1_2 = 5
        if row[2] in ["A"]:
            cent2_1 = 10
            cent2_2 = self.cent(8, 9)
            cent2_3 = self.cent(8, 9)
            cent2_4 = self.cent(8, 9)

            cent3_1 = 5
            cent3_2 = 5
            cent3_3 = 5

            cent4_1 = 13
            cent5_1 = self.cent(8, 9)
            cent6_1 = 4
            cent6_2 = 4

        elif row[2] in ["B"]:
            cent2_1 = 8
            cent2_2 = self.cent(7, 8)
            cent2_3 = self.cent(7, 8)
            cent2_4 = self.cent(4, 8)

            cent3_1 = 5
            cent3_2 = 4
            cent3_3 = 4

            cent4_1 = 10
            cent5_1 = self.cent(6, 9)
            cent6_1 = 4
            cent6_2 = 4

        elif row[2] in ["C"]:
            cent2_1 = 7
            cent2_2 = self.cent(6, 7)
            cent2_3 = self.cent(6, 7)
            cent2_4 = self.cent(4, 5)

            cent3_1 = 3
            cent3_2 = 3
            cent3_3 = 3

            cent4_1 = 8
            cent5_1 = self.cent(6, 7)
            cent6_1 = 3
            cent6_2 = 3
        else:
            cent2_1 = 7
            cent2_2 = self.cent(6, 7)
            cent2_3 = self.cent(6, 7)
            cent2_4 = self.cent(4, 5)

            cent3_1 = 3
            cent3_2 = 3
            cent3_3 = 3

            cent4_1 = 8
            cent5_1 = self.cent(6, 7)
            cent6_1 = 3
            cent6_2 = 3

        jieduan = (
            cent1_1
            + cent1_2
            + cent2_1
            + cent2_2
            + cent2_3
            + cent2_4
            + cent3_1
            + cent3_2
            + cent3_3
            + cent4_1
            + cent5_1
            + cent6_1
            + cent6_2
        )

        cents = []
        cents.append(row[0])
        cents.append(row[1])
        cents.append(row[2])
        cents.append(row[3])
        cents.append(jieduan)
        cents.append(cent1_1)
        cents.append(cent1_2)
        cents.append(cent2_1)
        cents.append(cent2_2)
        cents.append(cent2_3)
        cents.append(cent2_4)
        cents.append(cent3_1)
        cents.append(cent3_2)
        cents.append(cent3_3)
        cents.append(cent4_1)
        cents.append(cent5_1)
        cents.append(cent6_1)
        cents.append(cent6_2)

        return cents

    def homework_fun(self,row) -> list:

        if row[2] in ["A"]:
            cent1_1 = 100
            cent1_2 = 90
            cent1_3 = 95

        elif row[2] in ["B+"]:
            cent1_1 = 90
            cent1_2 = 80
            cent1_3 = 85
        elif row[2] in ["B"]:
            cent1_1 = 85
            cent1_2 = 75
            cent1_3 = 80
        elif row[2] in ["C+"]:
            cent1_1 = 80
            cent1_2 = 70
            cent1_3 = 75
        elif row[2] in ["C"]:
            cent1_1 = 75
            cent1_2 = 65
            cent1_3 = 70
        else:
            cent1_1 = 70
            cent1_2 = 60
            cent1_3 = 65

        avg = cent1_3
        cents = []
        cents.append(row[0])
        cents.append(row[1])
        cents.append(row[2])
        cents.append(row[3])
        cents.append(avg)
        cents.append(cent1_1)
        cents.append(cent1_2)
        cents.append(cent1_3)
        return cents

    def do(self) -> Path:
        rows = []
        # 缺省规则 例子 stu_23_1_java.csv
        input_file = Path("data").joinpath(f"{self.grd.value}").joinpath(f"stu_{self.grd.value}_{self.cls.value}_{self.course_name}.csv")
        self._check_file(input_file)
        with open(
            input_file,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.reader(file)
            rows = [row for row in reader]

        cents = []
        for i in range(len(rows)):
            line = []
            for j1 in range(self.sx_times):
                shixun_cents = self.shixu_fun(rows[i])
                # shixun_cents = self.jieduan_fun(rows[i])
                line.extend(shixun_cents)

            for j2 in range(self.xz_times):
                xiaozu_cents = self.xiaozu_fun(rows[i])
                line.extend(xiaozu_cents)

            jieke_cents = []
            if self.jieke_type == JieKeType.PAPER.value:
               jieke_cents = self.jieke_lunwen_fun(rows[i])
            else:
               jieke_cents = self.jieke_exam_fun(rows[i])
               
            line.extend(jieke_cents)
            if self.wk_times != 0:
                homework_cents = self.homework_fun(rows[i])
                line.extend(homework_cents)

            cents.append(line)
            
        timestamp =format_timestamp(datetime.now().timestamp() * 1000)
        # 缺省规则 例子 stu_23_1_java.csv
        output_file = Path("grade").joinpath(f"{self.grd.value}").joinpath(f"grd_{self.grd.value}_{self.cls.value}_{self.course_name}_{timestamp}.csv")
        self._check_file(output_file)
        with open(
            output_file,
            "a",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            writer = csv.writer(file)
            for row in cents:
                writer.writerow(row)
        self.logger.info(f"{self.course_name} : {output_file} has finish! -------- ")        

        return output_file

