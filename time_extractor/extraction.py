"""
@author: Rossi
@time: 2020-11-29

时间抽取模块
"""

import regex
from itertools import groupby
from operator import itemgetter
from .util import str2number, to_digit
import arrow
import traceback


class TimeExtractor:
    digit = "一二三四五六七八九十0-9壹贰叁肆伍陆柒捌玖零两"
    year = f"((?P<year>(?<![{digit}])[{digit}]{{4}}(?![{digit}]))|(?P<year>(?<![{digit}])[{digit}]{{2}})年)"
    month = f"((?P<month>(?<![{digit}])[{digit}]{{1,2}})(?![{digit}]))"
    day = f"((?P<day>(?<![{digit}])[{digit}]{{1,2}})(?![{digit}]))"
    reference = "(?P<ref>(这|上上个|上上|上个|上一个|上一|上|下下个|下下|下个|下一个|下一|下))"
    week = f"(?P<week>{reference}(周|星期)(?![{digit}日天末]))"
    weekday = f"(?P<weekday>({week}|{reference})?(星期|周)[{digit}日天])"
    weekend = f"(?P<weekend>{reference}?周末)"
    daysection = f"(?P<daysection>(破晓|凌晨|早晨|早上|明早|今早|早|上午|中午|午间|午后|下午|傍晚|黄昏|晚上|晚间|昨晚|明晚|今晚|晚|午夜|深夜|夜里))"
    time1 = f"((?P<hour>[{digit}]{{1,3}})[点|时])(?P<minute>([{digit}]{{1,3}}[分]?|半))?((?P<second>([{digit}]{{1,3}})秒))?"
    time2 = f"(?P<hour>(?<!\d)\d{{1,2}}(?!\d)):(?P<minute>(?<!\d)\d{{1,2}}(?!\d))"
    time = f"(?P<time>({time1}|{time2}))"
    referenceyear= "(?P<refyear>(去|前|今|明|后)年)"
    referencemonth= f"(?P<refmonth>{reference}月)"
    referenceday= "(?P<refday>(昨天|前天|今天|明天|后天))"

    date1 = f"{year}[年.-]?{month}[月.-]?{day}(日|号)?"
    date2 = f"({year}[年]?|{referenceyear}){month}月({day}(日|号))?"
    date3 = f"({month}月|{referencemonth}){day}(日|号)"
    date4 = f"({year}[年]?|{referenceyear})"
    date5 = f"({month}月|{referencemonth})"
    date6 = f"({day}(日|号)|{referenceday}|{weekday})"

    date = f"({date1}|{date2}|{date3}|{date4}|{date5}|{date6})"

    datetime = f"(?P<datetime>{date}({daysection}| )?{time}|{daysection}{time}|{time})"
    specific_daysection = f"(?P<specific_daysection>({date}|{referenceday}|{weekday})?{daysection}(?!{time}))"
    time_pattern = regex.compile(f"({datetime}|{specific_daysection}|{date}|{weekend}|{week})")
    time_range_pattern = regex.compile(f"(?P<datetime1>{date}?{time}|{date}{time}?)[到至-](?P<datetime2>{date}?{time}|{date}{time}?)")

    every_year = "(?P<YEAR>每年)"
    every_month = "(?P<MONTH>每[个]?月)"
    every_day = "(?P<DAY>每[一1]?天)"
    every_hour = "(?P<HOUR>每小时)"
    every_week = "(?P<WEEK>每(?=周)|每周)"
    workday = "(?P<WORKDAY>法定工作日)"
    weekday_ = "(?P<WEEKDAY>工作日)"
    datetime_ = f"(?P<datetime>({month}月)?({day}(日|号))?({daysection})?{time})"
    minute_second = f"(?P<ms>(?P<m>[{digit}]+)分((?P<s>[{digit}]+)秒)?)"
    time_cycle = regex.compile(f"({every_year}|{every_month}|{every_day}|{every_hour}|{every_week}|{workday}|{weekday_})({datetime_}|{minute_second})")

    ymd = f"((?P<year>[{digit}]+)年)?((?P<month>[{digit}]+)个月)?((?P<day>[{digit}]+)[天日])?"
    workday = f"(?P<weekday>[{digit}]+)[个]?工作日"
    weeks = f"(?P<week>[{digit}]+)(周|[个]?星期)"
    hms = f"((?P<hour>[{digit}]+)[个]?(小时|钟头|钟))?((?P<minute>[{digit}]+)(分钟|分))?((?P<second>[{digit}]+)秒)?"
    time_delta = regex.compile(f"(({workday}|{weeks}|{ymd}){hms}(后|之后|以后|过后)|过({workday}|{weeks}|{ymd}){hms})")

    def extract(self, text, base=None, range_mapping=None, handle_special_year=True):
        """从字符串中抽取时间

        Args:
            text (str): 字符串
            base (arrow.arrow.Arrow, optional): 时间基准
            range_mapping (dict, optional): 定义笼统时间的具体区间，即指定“早上、下午”等对应的时间，该参数为空时使用默认的定义
            handle_special_year(bool, optional): 指定是否处理特殊年份转化
        Yields:
            Time/TimeRange/TimeDelta/TimeCycle: 抽取的时间元素
        """
        covered = [0] * len(text)
        for item in self._extract_time_delta(text, covered):
            yield item
        for item in self._extract_time_cycle(text, covered, base):
            yield item
        for item in self._extract_time_range(text, covered, base, range_mapping):
            yield item
        for item in self._extract_time(text, covered, base, handle_special_year):
            yield item

    def _extract_time_delta(self, text, covered):
         for match in self._longest_match(self.time_delta.finditer(text)):
            if covered[match.start()] == 1:
                continue
            delta = TimeDelta.parse(match)
            if delta:
                for i in range(match.start(), match.end()):
                    covered[i] = 1
                yield delta
    
    def _extract_time_cycle(self, text, covered, base):
        for match in self._longest_match(self.time_cycle.finditer(text)):
            if covered[match.start()] == 1:
                continue
            cycle = TimeCycle.parse(match, base)
            if cycle:
                for i in range(match.start(), match.end()):
                    covered[i] = 1
                yield cycle
    
    def _extract_time_range(self, text, covered, base, range_mapping):
        for match in self._longest_match(self.time_range_pattern.finditer(text)):
            if covered[match.start()] == 0:
                for i in range(match.start(), match.end()):
                    covered[i] = 1
                yield TimeRange.parse(match, base, range_mapping)

    def _extract_time(self, text, covered, base, handle_special_year):
        for match in self._longest_match(self.time_pattern.finditer(text)):
            if covered[match.start()] == 1:
                continue
            group = None
            max_len = 0
            # 找到最长的分组
            for name, match_str in match.groupdict().items():
                if match_str is not None and len(match_str) > max_len:
                    group = name
                    max_len = len(match_str)
            if group is not None:
                if group not in ["weekend", "daysection", "specific_daysection", "week"]:
                    time = Time.parse(match, base, handle_special_year)
                    if time is not None:
                        yield time
                else:
                    time_range = TimeRange.parse(match, base, group)
                    if time_range is not None:
                        yield time_range
    
    def _longest_match(self, matches):
        matches = [(match.start(), match) for match in matches]
        for _, match_set in groupby(matches, itemgetter(0)):
            yield max(match_set, key=lambda x: len(x[1].group(0)))[1]        


class Time:
    mapping = {
        "year": {"去年": "-1", "明年": "+1", "前年": "-2", "今年": "+0"},
        "month": {"上个月": "-1", "下个月": "+1", "上月": "-1", "下月": "+1"},
        "day": {"昨天": "-1", "明天": "+1", "前天": "-2", "后天": "+2",
                "今天": "+0", "昨晚": "-1", "今晚": "+0", "明晚": "+1", "明早": "+1"},
        "weekday": {"一": "0", "二": "1", "三": "2", "四": "3", "五": "4", "六": "5", "日": "6", "天": "6"},
        "ref": {"上": "-", "上上": "--", "上个": "-", "上上个": "--", "上一个":"-", 
                "下": "+", "下下": "++", "下个":"+", "下下个": "++", "下一个": "-",
                "这": "", "这个": ""}
    }

    ref = regex.compile("上|上上|下|下下|这")

    def __init__(self, match=None):
        self.time_str = match.group() if match is not None else None
        self.match = match
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.second = None
        self.weekday = None

    @classmethod
    def from_arrow(cls, arrow_time):
        time = cls()
        time.year = arrow_time.year
        time.month = arrow_time.month
        time.day = arrow_time.day
        time.hour = arrow_time.hour
        time.minute = arrow_time.minute
        time.second = arrow_time.second
        return time
    
    def _addjust_with_time(self, time):
        self.year = time.year
        self.month = time.month if self.month is not None else None 
        self.day = time.day if self.day is not None else None
        self.hour = time.hour if self.hour is not None else None
        self.minute = time.minute if self.minute is not None else None
        self.second = time.second if self.second is not None else None
        self.weekday = None

    @staticmethod
    def normalize(time, base=None, handle_special_year=True):
        """进行时间标准化

        Args:
            time (Time): 抽取出来的原始时间
            base (datetime.datetime, optional): 时间基准
            handle_special_year (bool, optional): 指定是否处理特殊年份转换
        """
        if base is None:
            base = arrow.now()
        year_offset, month_offset, day_offset = None, None, None
        if time.year is None:
            time.year = base.year
        else:
            time.year, year_offset = Time.parse_number(time.year, base.year)

        if time.day is None and (time.hour is not None or time.minute is not None or time.second is not None or time.weekday is not None):
            time.day = base.day
        elif time.day is not None:
            time.day, day_offset = Time.parse_number(time.day, base.day)
        day_section = time.match.group("daysection")
        if day_section in ["今晚", "昨晚", "明晚", "明早"]:
            day_offset = int(Time.mapping["day"][day_section])

        if time.month is None and time.day is not None:
            time.month = base.month
        elif time.month is not None:
            time.month, month_offset  = Time.parse_number(time.month, base.month)

        if time.hour is not None and time.hour >= 24:
            time.hour -= 24
            if time.match.group("refday") is not None or day_section in ["今晚", "昨晚", "明晚"]:  # 昨天/今天/明天晚上3点
                day_offset = day_offset + 1 if day_offset is not None else 1
        time_ = Time._handle_offset(time, year_offset, month_offset, day_offset, base)
        if handle_special_year:
            if time_.year < 30:
                time_.year += 2000
            elif time_.year < 100:
                time_.year += 1900
        time._addjust_with_time(time_)
    
    @staticmethod
    def _verfiy(time):
        if time.year is not None  and time.month is None and time.day is not None:
            return False
        if time.hour is not None and time.minute is None and time.second is not None:
            return False
        if time.hour is not None and (time.year is not None or time.month is not None) and time.day is None:
            return False
        return True

    @staticmethod
    def _handle_offset(time, year_offset, month_offset, day_offset, base):
        time_ = time.to_arrow()
        if year_offset is not None:
            time_ = time_.shift(years=year_offset)
        if month_offset is not None:
            time_ = time_.shift(months=month_offset)
        if day_offset is not None:
            time_ = time_.shift(days=day_offset)
        if time.weekday is not None:
            day_offset = Time.compute_offset(time.weekday, base)
            time_ = time_.shift(days=day_offset)
        return time_

    @staticmethod
    def parse_number(target, base_num):
        offset = None
        if target.startswith("-"):
            num = base_num
            offset = - int(target[-1])
        elif target.startswith("+"):
            num = base_num
            offset = int(target[-1])
        else:
            num = str2number(target)
        return num, offset

    @staticmethod
    def compute_offset(weekday, base): 
        """计算与基准时间的偏移天数，要特别留意基准时间为“周日”时的处理。
        """
        if base.weekday() == 6 and not weekday.startswith("-") and not weekday.startswith("+"):  # 基准时间为周日
            day_offset = int(weekday) + 1 if weekday != "6" else 0
        else:
            day_offset = int(weekday[-1]) - base.weekday()
        week_offset = weekday.count("-") * -1 + weekday.count("+")
        if week_offset != 0:
            if base.weekday() == 6 and weekday[-1] != "6":  # 基准时间为周日
                week_offset += 1
            day_offset += 7 * week_offset
        return day_offset

    @staticmethod
    def parse(match, base=None, handle_special_year=True):
        try:
            time = Time(match)
            time.year = Time.parse_year(match)
            time.month = Time.parse_month(match)
            time.day = Time.parse_day(match)
            hour, minute, second = Time.parse_time(match)
            time.hour = hour
            time.minute = minute
            time.second = second
            time.weekday = Time.parse_weekday(match)
            if not Time._verfiy(time):
                return None
            Time.normalize(time, base, handle_special_year)
            return time
        except:
            traceback.print_exc()
            return None

    @staticmethod
    def parse_year(match):
        year = to_digit(match.group("year"))
        if year is None:
            year = match.group("refyear")
            if year is not None:
                year = Time.mapping["year"][year]
        return year

    @staticmethod
    def parse_month(match):
        month = match.group("month")
        if month is None:
            month = match.group("refmonth")
            if month is not None:
                month = Time.mapping["month"][month]
        return month
    
    @staticmethod
    def parse_day(match):
        day = match.group("day")
        if day is None:
            day = match.group("refday")
            if day is not None:
                day = Time.mapping["day"][day]
        return day

    @staticmethod
    def parse_weekday(match):
        weekday = match.group("weekday")
        if weekday is not None:
            ref = Time.ref.match(weekday)
            if ref is not None:
                weekday = Time.mapping["ref"][ref.group()] + Time.mapping["weekday"][weekday[-1]]
            else:
                weekday = Time.mapping["weekday"][weekday[-1]]
        return weekday

    @staticmethod
    def parse_time(match):
        hour = str2number(match.group("hour"))
        if hour == -1:
            hour = None
        elif hour <= 12 and match.group("daysection") is not None:
            section = match.group("daysection")
            if "晚" in section or "夜" in section: # 晚上6点->18点，晚上5点->29点（凌晨5点）
                hour = hour + 12 if hour > 5 else hour + 24
            elif section in ["下午", "午后"] and hour != 12:
                hour += 12
        minute = match.group("minute")
        if minute:
            if minute.endswith("分"):
                minute = str2number(minute[:-1])
            elif minute == "半":
                minute = 30
            else:
                minute = str2number(minute)
                if minute == -1:
                    minute = None
        second = str2number(match.group("second"))
        if second == -1:
            second = None
        return hour, minute, second

    def to_arrow(self):
        now = arrow.now()
        month = self.month or now.month
        day = self.day or now.day
        hour = self.hour or 0
        minute = self.minute or 0
        second = self.second  or 0
        return arrow.get(year=self.year, month=month, day=day, hour=hour, minute=minute, second=second)

    def __str__(self):
        return f"time:{self.time_str}"

    def to_dict(self):
        return {
            "type": "Time",
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "hour": self.hour,
            "minute": self.minute,
            "second": self.second,
            "weekday": self.weekday,
            "raw": self.time_str
        }


class TimeRange():
    range_mapping = {
        "昨晚": (-6, -19),
        "晚上": (18, 5), 
        "今晚": (18, 5),
        "明晚": (42, 29),
        "上午": (6, 11),
        "下午": (13, 17),
        "中午": (12, 12),
        "早上": (6, 9),
        "明早": (30, 33)
    }

    ref_mapping = {
        "这": 0,
        "上": -1,
        "上上": -2,
        "下": 1,
        "下下": 2
    }

    ref = regex.compile("上|上上|下|下下|这")

    def __init__(self, match=None, start=None, end=None):
        self.time_str = match.group() if match is not None else None
        self.match = match
        self.start = start
        self.end = end

    @staticmethod
    def parse(match, base=None, type_=None, range_mapping=None):
        if type_ is None:
            datetime1 = match.group("datetime1")
            datetime2 = match.group("datetime2")
            start = Time.parse(TimeExtractor.time_pattern.match(datetime1), base)
            match_ = TimeExtractor.time_pattern.match(datetime2)
            if match_.group("refyear") is not None or match_.group("refmonth") is not None or match_.group("refday") is not None:
                end = Time.parse(match_, base)
            else:
                end = Time.parse(match_, start.to_arrow())
            if start is not None and end is not None:
                return TimeRange(match, start, end)
        else:
            if base is None:
                base = arrow.now()
            return getattr(TimeRange, "parse_"+type_)(match, base)

    @staticmethod
    def parse_specific_daysection(match, base, range_mapping=None):
        time = Time.parse(match, base)
        if time.month is None:
            time.month = base.month
        if time.day is None:
            time.day = base.day
        section = match.group("daysection")
        range_mapping = range_mapping or TimeRange.range_mapping
        if section not in range_mapping:
            return None
        hour_range = range_mapping[section]
        start = time.to_arrow()
        end = time.to_arrow()
        if hour_range[0] < 0:
            start = start.shift(days=-1)
            start = start.replace(hour=hour_range[0]+24)
            end = end.shift(days=-1)
            end = end.replace(hour=hour_range[1]+24, minute=59)
        elif hour_range[0] > 24:
            start = start.shift(days=1)
            start = start.replace(hour=hour_range[0]-24)
            end = end.shift(days=1)
            end = end.replace(hour=hour_range[1]-24, minute=59)
        else:
            start = start.replace(hour=hour_range[0])
            end = end.replace(hour=hour_range[1], minute=59)
        if hour_range[1] < hour_range[0]:  # 晚上
            end = end.shift(days=1)
        start = Time.from_arrow(start)
        end = Time.from_arrow(end)
        time_range = TimeRange(match, start, end)
        return time_range

    @staticmethod
    def parse_daysection(match, base):
        return TimeRange.parse_specific_daysection(match, base)

    @staticmethod
    def parse_week(match, base):
        start = base.replace(hour=0, minute=0, second=0)
        day_offset = 0 if base.weekday() == 6 else -(base.weekday()+1)
        start = start.shift(days=day_offset)
        end = start.shift(days=6)
        ref = TimeRange.ref.match(match.group("week")).group()
        week_offset = TimeRange.ref_mapping[ref]
        if week_offset != 0:
            start = start.shift(weeks=week_offset)
            end = end.shift(weeks=week_offset)
        start = Time.from_arrow(start)
        end = Time.from_arrow(end)
        time_range = TimeRange(match, start, end)
        return time_range

    @staticmethod
    def parse_weekend(match, base):
        time = base.replace(hour=0, minute=0, second=0)
        if base.weekday() == 6:
            start = time.shift(days=-1)
        else:
            start = time.shift(weekday=5)
        end = start.shift(days=1, hours=23, minutes=59)
        ref = TimeRange.ref.match(match.group())
        ref = ref.group() if ref is not None else ""
        week_offset = TimeRange.ref_mapping[ref] if ref != "" else 0
        if week_offset != 0:
            start = start.shift(weeks=week_offset)
            end = end.shift(weeks=week_offset)
        start = Time.from_arrow(start)
        end = Time.from_arrow(end)
        time_range = TimeRange(match, start, end)
        return time_range

    def __str__(self):
        return f"timerange:{self.time_str}"
    
    def to_dict(self):
        return {
            "type": "TimeRange",
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "raw": self.time_str
        }


class TimeDelta:
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"
    WEEKDAY = "weekday"
    WEEK = "week"

    def __init__(self):
        self.years = 0
        self.months = 0
        self.days = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.weekdays = 0
        self.weeks = 0
        self.time_str = None 
        self.match = None

    @classmethod
    def parse(cls, match):
        keys = [cls.YEAR, cls.MONTH, cls.DAY, cls.HOUR, cls.MINUTE, cls.SECOND, cls.WEEK, cls.WEEKDAY]
        groupdict = match.groupdict()
        if not any(groupdict[k] for k in keys):
            return None
        delta = cls()
        delta.years = max(str2number(groupdict[cls.YEAR]), 0)
        delta.months = max(str2number(groupdict[cls.MONTH]), 0)
        delta.days = max(str2number(groupdict[cls.DAY]), 0)
        delta.hours = max(str2number(groupdict[cls.HOUR]), 0)
        delta.minutes = max(str2number(groupdict[cls.MINUTE]), 0)
        delta.seconds = max(str2number(groupdict[cls.SECOND]), 0)
        delta.weekdays = max(str2number(groupdict[cls.WEEKDAY]), 0)
        delta.weeks = max(str2number(groupdict[cls.WEEK]), 0)
        delta.time_str = match.group()
        delta.match = match
        return delta

    def __str__(self):
        return f"time delta: {self.time_str}"
    
    def to_dict(self):
        return {
            "type": "TimeDelta",
            "years": self.years,
            "months": self.months,
            "days": self.days,
            "hours": self.hours,
            "minutes": self.minutes,
            "seconds": self.seconds,
            "weeks": self.weeks,
            "weekday": self.weekdays,
            "raw": self.time_str
        }


class TimeCycle:
    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    WEEK = "WEEK"
    WEEKDAY = "WEEKDAY"
    WORKDAY = "WORKDAY"

    def __init__(self):
        self.unit = None
        self.time = None
        self.time_str = None
        self.match = None

    @classmethod
    def parse(cls, match, base=None):
        keys = [cls.YEAR, cls.MONTH, cls.DAY, cls.HOUR, cls.MONTH, cls.WEEKDAY, cls.WORKDAY, cls.WEEK]
        groupdict = match.groupdict()
        if not any(groupdict[k] for k in keys):
            return None 
        cycle = TimeCycle()
        for key in keys:
            if groupdict[key]:
                cycle.unit = key
                break
        datetime = groupdict["datetime"]
        if datetime is not None:
            datetime = TimeExtractor.time_pattern.match(datetime)
            cycle.time = Time.parse(datetime, base)
        else:
            minute = groupdict["m"]
            second = groupdict["s"]
            time = Time()
            time.minute = minute
            time.second = second
            cycle.time = time
        cycle.time_str = match.group()
        cycle.match = match
        return cycle
    
    def to_dict(self):
        return {
            "type": "TimeCycle",
            "unit": self.unit,
            "time": self.time.to_dict(),
            "raw": self.time_str
        }
