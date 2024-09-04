# SUSTech 教务系统导出 ics文件

---

#### 由于学校教务系统导出课表没有ics选项，使用Google Calendar很不自在，自己写了脚本自用（虽然效率不高）

#### 本项目基于[@Frank Wu](https://github.com/GhostFrankWu)所编写的选课助手[SUSTech_Tools](https://github.com/GhostFrankWu/SUSTech_Tools)。

---

## 使用说明

#### 直接运行`main.py`即可，根据提示填写信息即可生成ics文件（默认为`courses.ics`），内容如下：

```txt
BEGIN:VCALENDAR
SUMMARY: 中国马克思主义与当代
DTSTART: 20240910T190000
DTEND: 20240910T205000
LOCATION: 商学院101
DESCRIPTION: 中国马克思主义与当代
DTSTAMP: 20240904T212257
BEGIN:VEVENT
SUMMARY:中国马克思主义与当代
DTSTART:20240910T190000
DTEND:20240910T205000
LOCATION:商学院101
DESCRIPTION:中国马克思主义与当代
DTSTAMP:20240904T212257
END:VEVENT
END:VCALENDAR
...
```
#### 之后即可导入Google Calendar等日历。