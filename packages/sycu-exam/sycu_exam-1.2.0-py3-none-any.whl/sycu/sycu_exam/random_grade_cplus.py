
import csv
import random

from datetime import datetime
from sycu.libs.time_tools import format_timestamp
from sycu.libs.log_tools import logger

c_name = "stu_23sk-1-java"

sx_times = 1
xz_times = 1


def jieke_fun(row):
    jieke = 0
    cent1_1 = 5
    cent1_2 = 5
    if row[2] in ["A"]:
        cent2_1 = 10
        cent2_2 = cent(8, 9)
        cent2_3 = cent(8, 9)
        cent2_4 = cent(8, 9)

        cent3_1 = 5
        cent3_2 = 5
        cent3_3 = 5
        # cent3_4 = cent(3, 4)

        cent4_1 = 14
        cent5_1 = cent(8, 9)
        cent6_1 = 5
        cent6_2 = 5
    elif row[2] in ["B+"]:
        cent2_1 = cent(7, 8)
        cent2_2 = cent(7, 8)
        cent2_3 = cent(7, 8)
        cent2_4 = cent(7, 8)

        cent3_1 = 5
        cent3_2 = 5
        cent3_3 = 5
        # cent3_4 = cent(3, 4)

        cent4_1 = 12
        cent5_1 = cent(8, 9)
        cent6_1 = 5
        cent6_2 = 5
    elif row[2] in ["B"]:
        cent2_1 = cent(6, 7)
        cent2_2 = cent(6, 7)
        cent2_3 = cent(7, 8)
        cent2_4 = cent(7, 8)

        cent3_1 = 5
        cent3_2 = 4
        cent3_3 = 5
        # cent3_4 = cent(3, 4)

        cent4_1 = 11
        cent5_1 = cent(8, 9)
        cent6_1 = 5
        cent6_2 = 5
    elif row[2] in ["C+"]:
        cent2_1 = cent(7, 8)
        cent2_2 = cent(6, 7)
        cent2_3 = cent(6, 7)
        cent2_4 = cent(3, 4)

        cent3_1 = 5
        cent3_2 = 4
        cent3_3 = 4
        # cent3_4 = cent(2, 3)

        cent4_1 = 9
        cent5_1 = cent(6, 7)
        cent6_1 = 4
        cent6_2 = 4
    elif row[2] in ["C"]:
        cent2_1 = cent(7, 8)
        cent2_2 = cent(6, 7)
        cent2_3 = cent(6, 7)
        cent2_4 = cent(4, 5)

        cent3_1 = 3
        cent3_2 = 3
        cent3_3 = 3
        # cent3_4 = cent(2, 3)

        cent4_1 = 7
        cent5_1 = cent(6, 7)
        cent6_1 = 3
        cent6_2 = 3
    else:
        cent2_1 = cent(6, 7)
        cent2_2 = cent(6, 7)
        cent2_3 = cent(6, 7)
        cent2_4 = 0

        cent3_1 = 3
        cent3_2 = 3
        cent3_3 = 3
        # cent3_4 = cent(2, 3)

        cent4_1 = 5
        cent5_1 = cent(5, 6)
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
        # + cent3_4
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
    # cents.append(cent3_4)
    cents.append(cent4_1)
    cents.append(cent5_1)
    cents.append(cent6_1)
    cents.append(cent6_2)

    return cents


def xiaozu_fun(row):
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
        cent6_1 = cent(9, 10)
        cent7_1 = cent(9, 10)
        cent8_1 = cent(8, 9)

    elif row[2] in ["B+"]:
        cent6_1 = cent(8, 9)
        cent7_1 = cent(8, 9)
        cent8_1 = cent(8, 9)
    elif row[2] in ["B"]:
        cent6_1 = cent(6, 8)
        cent7_1 = cent(6, 8)
        cent8_1 = cent(6, 8)
    elif row[2] in ["C+"]:
        cent6_1 = cent(5, 7)
        cent7_1 = cent(5, 7)
        cent8_1 = cent(5, 7)
    elif row[2] in ["C"]:
        cent6_1 = cent(4, 5)
        cent7_1 = cent(4, 5)
        cent8_1 = cent(4, 5)
    else:
        cent6_1 = cent(3, 4)
        cent7_1 = cent(3, 4)
        cent8_1 = cent(3, 4)

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


def shixu_fun(row):
    shixun = 0
    cent1_1 = 10
    # cent1_2 = 5
    if row[2] in ["A"]:
        cent2_1 = 12
        cent2_2 = 15
        cent2_3 = 5
        cent2_4 = 15
        # cent2_5 = 10
        # cent2_6 = cent(10, 12)
        cent3_1 = 10
        cent4_1 = cent(13, 15)
        cent5_1 = 9
    elif row[2] in ["B+"]:
        cent2_1 = 12
        cent2_2 = 15
        cent2_3 = 5
        cent2_4 = cent(12, 14)
        # cent2_5 = 10
        # cent2_6 = cent(8, 10)
        cent3_1 = 10
        cent4_1 = cent(13, 15)
        cent5_1 = cent(7, 8)
    elif row[2] in ["B"]:
        cent2_1 = 12
        cent2_2 = 10
        cent2_3 = 5
        cent2_4 = cent(12, 14)
        # cent2_5 = 10
        # cent2_6 = cent(8, 10)
        cent3_1 = 10
        cent4_1 = cent(13, 15)
        cent5_1 = cent(7, 8)
    elif row[2] in ["C+"]:
        cent2_1 = 9
        cent2_2 = 10
        cent2_3 = 0
        cent2_4 = cent(12, 14)
        # cent2_5 = 10
        # cent2_6 = cent(8, 10)
        cent3_1 = 10
        cent4_1 = cent(12, 13)
        cent5_1 = cent(7, 8)
    elif row[2] in ["C"]:
        cent2_1 = 9
        cent2_2 = 5
        cent2_3 = 0
        cent2_4 = cent(12, 14)
        # cent2_5 = 10
        # cent2_6 = cent(8, 10)
        cent3_1 = 10
        cent4_1 = cent(10, 13)
        cent5_1 = cent(7, 8)
    else:
        cent2_1 = 6
        cent2_2 = 5
        cent2_3 = 0
        cent2_4 = cent(10, 12)
        # cent2_5 = 10
        # cent2_6 = cent(8, 10)
        cent3_1 = 10
        cent4_1 = cent(8, 10)
        cent5_1 = cent(7, 8)

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
    # cents.append(cent1_2)
    cents.append(cent2_1)
    cents.append(cent2_2)
    cents.append(cent2_3)
    cents.append(cent2_4)
    # cents.append(cent2_5)
    # cents.append(cent2_6)
    cents.append(cent3_1)
    cents.append(cent4_1)
    cents.append(cent5_1)
    # print(
    #     row[1],
    #     row[2],
    #     shixun,
    #     cent1_1,
    #     cent1_2,
    #     cent2_1,
    #     cent2_2,
    #     cent2_3,
    #     cent2_4,
    #     cent2_5,
    #     cent2_6,
    #     cent3_1,
    #     cent4_1,
    #     cent5_1,
    #     sep=",",
    # )

    return cents


def homework_fun(row):
    work = 0

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

    work = cent1_3
    cents = []
    cents.append(row[0])
    cents.append(row[1])
    cents.append(row[2])
    cents.append(row[3])
    cents.append(work)
    cents.append(cent1_1)
    cents.append(cent1_2)
    cents.append(cent1_3)
    return cents


def cent(low, high):
    cent = random.randint(low, high)
    return cent


def do():
    rows = []
    with open(
        "{0}/../grade/{1}.csv".format(data_path, c_name),
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)
        rows = [row for row in reader]

    cents = []
    for i in range(len(rows)):
        line = []
        for j1 in range(sx_times):
            shixun_cents = shixu_fun(rows[i])
            line.extend(shixun_cents)

        for j2 in range(xz_times):
            xiaozu_cents = xiaozu_fun(rows[i])
            line.extend(xiaozu_cents)

        jieke_cents = jieke_fun(rows[i])
        line.extend(jieke_cents)

        homework_cents = homework_fun(rows[i])
        line.extend(homework_cents)

        cents.append(line)

    with open(
        "{0}/../grade/{3}_{1}_{2}.csv".format(
            data_path,
            "gd",
            c_name,
            format_timestamp(datetime.now().timestamp() * 1000),
        ),
        "a",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.writer(file)
        for row in cents:
            writer.writerow(row)


if __name__ == "__main__":
    logger.info("random_grade Starting ...... ")
    do()
