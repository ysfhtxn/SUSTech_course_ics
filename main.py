from getpass import getpass
from json import loads
import re

from datetime import datetime, timedelta, timezone

import requests
from colorama import init

from dateutil.relativedelta import relativedelta

import sys
import warnings
from urllib3.exceptions import InsecureRequestWarning


def warn(message, category, filename, lineno, file=None, line=None):
    if category is not InsecureRequestWarning:
        sys.stderr.write(warnings.formatwarning(message, category, filename, lineno, line))


warnings.showwarning = warn

head = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}


def cas_login(user_name, pwd):
    """ 
    用于和南科大CAS认证交互，拿到tis的有效cookie
    输入用于CAS登录的用户名密码，输出tis需要的全部cookie内容(返回头Set-Cookie段的route和jsessionid)
    我的requests的session不吃CAS重定向给到的cookie，不知道是代码哪里的问题，所以就手动拿了 
    
    Author:  @FrankWu https://github.com/GhostFrankWu
    """
    print("[\x1b[0;36m!\x1b[0m] " + "测试CAS链接...")
    try:  # Login 服务的CAS链接有时候会变
        login_url = "https://cas.sustech.edu.cn/cas/login?service=https%3A%2F%2Ftis.sustech.edu.cn%2Fcas"
        # login_url = "https://cas.sustech.edu.cn/cas/clientredirect?client_name=Wework&service=https%3A%2F%2Ftis.sustech.edu.cn%2Fcas"
        req = requests.get(login_url, headers=head, verify=False)
        assert (req.status_code == 200)
        print("[\x1b[0;32m+\x1b[0m] " + "成功连接到CAS...")
    except:
        print("[\x1b[0;31mx\x1b[0m] " + "不能访问CAS, 请检查您的网络连接状态")
        return "", ""
    print("[\x1b[0;36m!\x1b[0m] " + "登录中...")
    data = {  # execution大概是CAS中前端session id之类的东西
        'username': user_name,
        'password': pwd,
        'execution': str(req.text).split('''name="execution" value="''')[1].split('"')[0],
        '_eventId': 'submit',
    }
    req = requests.post(login_url, data=data, allow_redirects=False, headers=head, verify=False)
    if "Location" in req.headers.keys():
        print("[\x1b[0;32m+\x1b[0m] " + "登录成功")
    else:
        print("[\x1b[0;31mx\x1b[0m] " + "用户名或密码错误，请检查")
        return "", ""
    req = requests.get(req.headers["Location"], allow_redirects=False, headers=head, verify=False)

    route_ = re.findall('route=(.+?);', req.headers["Set-Cookie"])[0]
    jsessionid = re.findall('JSESSIONID=(.+?);', req.headers["Set-Cookie"])[0]
    return route_, jsessionid

def make_ics(courses_list):
    course_pattern = r'^(.*?):'       # 匹配课程名字
    time_pattern = r'(\d{2}:\d{2})-(\d{2}:\d{2})'  # 匹配时间段

    def to_vcs_format(dt: datetime) -> str:
        return dt.strftime('%Y%m%dT%H%M%S')

    beijing_tz = timezone(timedelta(hours=8))

    ics_info = []
    for entry in courses_list:
        name_match = re.search(course_pattern, entry['BT'])
        time_match = re.search(time_pattern, entry['BT'])
        if name_match and time_match:
            course_name = name_match.group(1)
            start_time_str = time_match.group(1)
            end_time_str = time_match.group(2)
            date_str = entry['SJ']
            start_datetime = datetime.strptime(f"{date_str} {start_time_str}", '%Y-%m-%d %H:%M').replace(tzinfo=beijing_tz)
            end_datetime = datetime.strptime(f"{date_str} {end_time_str}", '%Y-%m-%d %H:%M').replace(tzinfo=beijing_tz)
            course_info = {
                'SUMMARY': course_name,
                'DTSTART': to_vcs_format(start_datetime),
                'DTEND': to_vcs_format(end_datetime),
                'LOCATION': entry['NR'],
                'DESCRIPTION': entry['KCMC'],
                'DTSTAMP': to_vcs_format(datetime.now(beijing_tz))
            }
            ics_info.append(course_info)
    return ics_info

if __name__ == '__main__':
    init(autoreset=True)  # 某窗口系统的优质终端并不直接支持如下转义彩色字符，所以需要一些库来帮忙
    # 下面是CAS登录
    route, JSESSIONID = "", ""
    while route == "" or JSESSIONID == "":
        userName = input("请输入您的学号：")  # getpass在PyCharm里不能正常工作，请改为input或写死
        passWord = getpass("请输入CAS密码（密码不显示，输入完按回车即可）：")
        route, JSESSIONID = cas_login(userName, passWord)
        if route == "" or JSESSIONID == "":
            print("[\x1b[0;33m-\x1b[0m] " + "请重试...")
    head['cookie'] = f'route={route}; JSESSIONID={JSESSIONID};'
    
    stYEAR = input("本学期第一周所在年：")
    stMONTH = input("本学期第一周所在月：")
    print("[\x1b[0;36m!\x1b[0m] " + "获取日程中...")
    initial_date = datetime(int(stYEAR), int(stMONTH), 1)
    courses_list = []
    for _ in range(5):
        current_month_date = initial_date + relativedelta(months=_)
        new_date = str(int(current_month_date.strftime('%Y'))) + '-' + str(int(current_month_date.strftime('%m'))) + '-' + str((current_month_date.strftime('%d')))
        semester_info = loads(
            requests.post('https://tis.sustech.edu.cn/component/querygrrclist', data={"rcrq": new_date}, headers=head, verify=False).text)
        days = [int(info['D']) for info in semester_info]
        for day in days:
            new_date = str(int(current_month_date.strftime('%Y'))) + '-' + str(int(current_month_date.strftime('%m'))) + '-' + str(day)
            semester_info = loads(
                requests.post('https://tis.sustech.edu.cn/component/queryrcxxlist', data={"rcrq": new_date}, headers=head, verify=False).text)
            courses_list.append(semester_info[0])
    print("[\x1b[0;32m+\x1b[0m] " + "获取日程成功")
    
    ics_name = 'courses.ics'
    print("[\x1b[0;36m!\x1b[0m] " + f"生成{ics_name}中...")
    ics_info = make_ics(courses_list)
    with open('courses.ics', 'w') as f:
        f.write("BEGIN:VCALENDAR\n")
        for course in ics_info:
            f.write(f"SUMMARY: {course['SUMMARY']}\n")
            f.write(f"DTSTART: {course['DTSTART']}\n")
            f.write(f"DTEND: {course['DTEND']}\n")
            f.write(f"LOCATION: {course['LOCATION']}\n")
            f.write(f"DESCRIPTION: {course['DESCRIPTION']}\n")
            f.write(f"DTSTAMP: {course['DTSTAMP']}\n")
            f.write("BEGIN:VEVENT\n")
            f.write(f"SUMMARY:{course['SUMMARY']}\n")
            f.write(f"DTSTART:{course['DTSTART']}\n")
            f.write(f"DTEND:{course['DTEND']}\n")
            f.write(f"LOCATION:{course['LOCATION']}\n")
            f.write(f"DESCRIPTION:{course['DESCRIPTION']}\n")
            f.write(f"DTSTAMP:{course['DTSTAMP']}\n")
            f.write("END:VEVENT\n")
        f.write("END:VCALENDAR\n")
    print("[\x1b[0;32m+\x1b[0m] " + f"生成{ics_name}成功")