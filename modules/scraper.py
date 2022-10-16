import requests
import re
from lxml import html

from dateutil import parser
from datetime import datetime, time
from timeframe import TimeFrame

from modules.course import Course

from cachetools.func import ttl_cache as cache

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Accept-Language": "en-US,en;q=0.5",
}
QUARTERS = ["WIN", "SPR", "SUM", "AUT"]


@cache(maxsize=1, ttl=10 * 60)
def get_quarter_dates():
    webpage = requests.get("https://www.washington.edu/students/reg/begendcal.html", headers=HEADERS)
    tree = html.fromstring(webpage.text)

    quarter_times = {}
    for row in tree.xpath("//table[1]//tr[position() > 1 and position() <= last() - 2]"):
        for qtr in QUARTERS:
            if row.xpath("th/text()")[0].upper().startswith(qtr):
                quarter_times[qtr] = TimeFrame(
                    parser.parse(row.xpath("td[1]/text()")[0]),
                    parser.parse(row.xpath("td[2]/text()")[0]),
                )
                break
    return quarter_times


def get_current_quarter():
    now = datetime.now()
    quarter_times = get_quarter_dates()
    for qtr, timeframe in quarter_times.items():
        if timeframe.start <= now <= timeframe.end:
            return qtr
    return None


def get_current_quarter_year(digits=2):
    return get_current_quarter() + str(datetime.now().year)[-digits:]


@cache(maxsize=1, ttl=10 * 60)
def get_programpage_urls():
    url = f"https://www.washington.edu/students/timeschd/{get_current_quarter_year(4)}"
    webpage = requests.get(url, headers=HEADERS)
    tree = html.fromstring(webpage.text)
    refs = tree.xpath('//div[contains(@class, "uw-body")]//ul//a[contains(@href,".html")]/@href')
    return [f"{url}/{ref}" for ref in refs]


@cache(maxsize=1, ttl=10 * 60)
def parse_programpage(url):
    webpage = requests.get(url, headers=HEADERS)
    tree = html.fromstring(webpage.text)

    for cls in tree.xpath("//table//pre/a/.."):
        header = cls.xpath('ancestor::table/preceding-sibling::table[position() < 2]//a[contains(@href,".html")]')
        if not header:
            continue

        info_anchor = "https://www.washington.edu" + header[0].get("href")
        info = get_course_info(info_anchor)
        found_clses = parse_cls(cls)
        if not info or not found_clses:
            continue

        for found_cls in found_clses:
            dates = get_quarter_dates()[get_current_quarter()]
            course = Course(info["name"], info["desc"], f'{found_cls["loc"]} {found_cls["room"]}', found_cls["cap"])
            course.set_dates(dates.start, dates.end)
            course.set_days(found_cls["days"])

            if found_cls["time"]:
                course.set_time(found_cls["time"][0], found_cls["time"][1])

            yield course


def get_course_info(course_anchor: str):
    base, cls_id = course_anchor.split("#")
    dep_info = get_dep_infos(base)
    if cls_id in dep_info:
        return dep_info[cls_id]


@cache(maxsize=512, ttl=10 * 60)
def get_dep_infos(dep_url: str):
    # https://www.washington.edu/students/crscat/anthro.html
    webpage = requests.get(dep_url, headers=HEADERS)
    tree = html.fromstring(webpage.text)
    raw_courses = tree.xpath("body/*[@name]")

    courses = dict()
    for course in raw_courses:
        course_id = " ".join(course.xpath("@name"))
        course_name = " ".join(course.xpath("./p/b/text()"))
        course_desc = " ".join(course.xpath("./p/text()"))

        # Remove shit from name
        course_name = re.sub(r"(\(.*\))|A&H|SSc|NSc|RSN|DIV", "", course_name)
        course_name = re.sub(r"(\s+[-.:,+^]*\s+)+|(\s+)", " ", course_name).strip()

        courses[course_id] = {
            "name": course_name,
            "desc": course_desc,
        }
    return courses


def parse_cls(cls):
    raw_str = cls.xpath("string()")

    # Drop all lines in all caps: they are descriptions
    cls_strs = re.sub(r"^([A-Z0-9]|\s|[^\w\s])+$", "", raw_str, flags=re.MULTILINE)
    cls_strs = cls_strs.splitlines()

    cls_infos = list()
    for line in filter(lambda x: x.strip(), cls_strs):
        days = parse_cls_day(line[24:31].strip())
        time = parse_cls_times(line[31:41].strip())
        loc = line[41:45].strip()
        room = line[45:53].strip()
        cap = parse_cls_capacity(line[92:100].strip())

        course = dict()
        if len(cls_infos) > 0:
            course = cls_infos[0]

        course["days"] = days
        course["time"] = time
        course["loc"] = loc
        course["room"] = room
        course["cap"] = cap

        for k, v in course.items():
            if not re.search(r"\w", str(v)):
                course[k] = None

        cls_infos.append(course)

    return cls_infos


def parse_cls_capacity(cls_cap_str: str):
    cls_cap_str = re.sub(r"[^\d/]", "", cls_cap_str)
    if "/" not in cls_cap_str:
        return None

    students, seats = cls_cap_str.split("/")
    return students, seats


def parse_cls_times(time_str: str):
    if "-" not in time_str or not re.search(r"\d", time_str):
        return None

    pm = True

    start, end = time_str.split("-")
    start_hrs, end_hrs = int(start[:-2]), int(re.sub(r"[^\d]", "", end)[:-2])

    # Times are super weird. 1:30pm is listed as 130-320
    # but 4:30pm is listed as 430-620P
    # Assume PM and if time is small (4-12) and does not have a P,
    # then it is AM
    if 4 <= start_hrs <= 12 and "p" not in time_str.lower():
        pm = False

    # Another issue: if we're in AM, we might be listed as 1130-120
    # Obviously, this isn't 11:30am-1:20am, so we add 12hrs to end time
    if not pm and end_hrs < start_hrs:
        end_hrs += 12

    start = re.sub(r"p|P", "", start)
    end = re.sub(r"p|P", "", end)

    # Convert to 24 hour time
    if pm:
        start_hrs += 12
        end_hrs += 12
    start_hrs, end_hrs = start_hrs % 24, end_hrs % 24

    start_mins = int(start[-2:])
    end_mins = int(end[-2:])

    return time(start_hrs, start_mins), time(end_hrs, end_mins)


def parse_cls_day(cls_day_str: str):
    if "to be" in cls_day_str:
        return None
    if "arran" in cls_day_str:
        return None

    days = list()
    if "Su" in cls_day_str:
        cls_day_str.replace("Su", "")
        days.append(6)
    if "S" in cls_day_str:
        days.append(5)
    if "F" in cls_day_str:
        days.append(4)
    if "Th" in cls_day_str:
        cls_day_str.replace("Th", "")
        days.append(3)
    if "W" in cls_day_str:
        days.append(2)
    if "T" in cls_day_str:
        days.append(1)
    if "M" in cls_day_str:
        days.append(0)
    return days


def get_all_classes():
    for url in get_programpage_urls():
        for course in parse_programpage(url):
            yield course
