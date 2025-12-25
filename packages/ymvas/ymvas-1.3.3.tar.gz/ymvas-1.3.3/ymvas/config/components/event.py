from functools import lru_cache
from os.path import basename
from datetime import date, datetime
import uuid, hashlib

from croniter import croniter
from dateutil import parser
from ymvas.utils.files import get_yaml


class Event:
    DAYS = ['SU','MO','TU','WE','TH','FR','SA']

    def __init__(self, src: str | None = None ) -> None:
        self.src = src

        if src is None:
            self._data = {}
            return

        self._data = get_yaml( src )


    def clear_caches(self) -> None:
        for attr in dir(self):
            fn = getattr(self, attr)
            if callable(fn) and hasattr(fn, "cache_clear"):
                fn.cache_clear()

    @property
    def data(self) -> dict:
        return self._data

    @property
    @lru_cache
    def name(self) -> str | None:
        data = self.data
        if 'name' in data:
           return str(data['name'])

        if self.src is None:
            return

        _name = basename(self.src)
        _name = _name.split('.')[0]
        return _name

    @property
    @lru_cache
    def description(self) -> str | None:
        data = self.data
        if 'description' in data:
            return str(data['description'])


    @property
    @lru_cache
    def uid(self) -> str:
        if self.src is None:
            return str(uuid.uuid4())
        return hashlib.md5(
            self.src.encode('utf-8')
        ).hexdigest()

    @property
    @lru_cache
    def active(self) -> bool:
        if not 'active' in self.data:
            return False

        active = self.data.get('active')

        # manual deactivation checks
        if isinstance(active,int) and active != 1:
            return False
        if isinstance(active,bool) and not active:
            return False
        if isinstance(active,str) and active.lower() != 'true':
            return False

        # structure deactivation checks
        if self.name is None:
            return False
        if self.start is None:
            return False


        return True

    @property
    @lru_cache
    def priority(self) -> int | None:
        u = self.data.get('priority',0)
        if str(u).isnumeric():
            return int(u)
        return None

    @property
    @lru_cache
    def cron_expr(self) -> str | None:
        if not 'cron' in self.data:
            return None
        return str(self.data['cron'])

    @property
    @lru_cache
    def cron_data(self) -> tuple[list[list[str]],dict[str,set[int]]] | None:
        if self.cron_expr is None:
            return

        if not croniter.is_valid(self.cron_expr):
            return

        return croniter.expand(self.cron_expr)

    @property
    @lru_cache
    def is_all_day(self) -> bool:
        data = self.data
        if not 'is-all-day' in data:
            return False

        _is = data['is-all-day']
        if isinstance(_is,bool):
            return _is

        if isinstance(_is,str):
            _is = _is.lower().strip()
            return _is == "true" or _is == '1'

        if isinstance(_is,int):
            return _is == 1

        return False

    @property
    @lru_cache
    def frequency(self) -> str | None:
        data = self.data

        # explicit frequency
        if "frequency" in data and isinstance(data['frequency'],str):
            valid_1 = [
                "YEARLY",
                "MONTHLY",
                "WEEKLY",
                "DAILY",
            ]
            valid_2 = [
                "HOURLY",
                "MINUTELY",
                "SECONDLY",
            ]

            valid = valid_1 + valid_2

            freq = data["frequency"].upper()
            freq = freq if freq in valid else None

            if self.is_all_day and freq in valid_2:
                return None

            return freq

        # infer from cron
        cron = self.cron_data
        if cron is None:
            return None

        minute, hour, day, month, weekday = cron[0]
        if month != ["*"] and day != ["*"]:
            return "YEARLY"
        if day != ["*"] and weekday == ["*"]:
            return "MONTHLY"
        if weekday != ["*"]:
            return "WEEKLY"

        if self.is_all_day:
            return "DAILY"

        if hour != ["*"] or minute != ["*"]:
            if hour != ["*"] and minute == ["*"]:
                return "HOURLY"
            if minute != ["*"] and hour == ["*"]:
                return "MINUTELY"
            return "DAILY"
        return "SECONDLY"

    @property
    @lru_cache
    def interval(self) -> int | None:
        data = self.data
        if "interval" in data:
            try:
                v = int(data["interval"])
                return v if v > 0 else None
            except:
                return None
        return None

    @property
    @lru_cache
    def by_month(self) -> list[int] | None:
        data = self.data

        if 'by-month' in data:
            bmonth = data['by-month']
            def _valid(x) -> bool:
                if not isinstance(x,(str,int)):
                    return False
                if not str(x).isnumeric():
                    # TODO ALLOW FOR TEXT MONTHS
                    return False
                iv = int(x)
                if not( 1 <= iv <= 12 ):
                    return False
                return True

            if isinstance(bmonth,str) and ',' in bmonth:
                bmonth = bmonth.split(',')
                bmonth = list(d.strip() for d in bmonth)

            if isinstance(bmonth,list):
                res = [int(v) for v in bmonth if _valid(v)]
                if len(res) != 0:
                    return list(res)

            elif _valid(bmonth):
                return [int(bmonth)]

        cron = self.cron_data
        if cron is None:
            return None

        minute, hour, day, month, weekday = cron[0]
        if month != ["*"]:
            return [int(m) for m in month]

        return list(range(1,13))

    @property
    @lru_cache
    def by_month_day(self) -> list[int] | None:
        data = self.data

        if 'by-month-day' in data:
            bmonth = data['by-month-day']
            def _valid(x) -> bool:
                if not isinstance(x,(str,int)):
                    return False
                if not str(x).isnumeric():
                    return False
                iv = int(x)
                if not ( -31 <= iv <= 31 and iv != 0 ):
                    return False
                return True

            if isinstance(bmonth,str) and ',' in bmonth:
                bmonth = bmonth.split(',')
                bmonth = list(d.strip() for d in bmonth)

            if isinstance(bmonth,list):
                res = [int(v) for v in bmonth if _valid(v)]
                if len(res) != 0:
                    return list(res)

            elif _valid(bmonth):
                return [int(bmonth)]

        cron = self.cron_data
        if cron is None:
            return None

        minute, hour, day, month, weekday = cron[0]
        if day != ["*"]:
            return [int(d) for d in day]

        return list(range(1, 32))

    @property
    @lru_cache
    def by_day(self) -> list[str] | None:
        data = self.data
        if "by-day" in data:
            bday = data['by-day']

            def _valid(x) -> bool:
                if isinstance(x, int):
                    if 0 <= x <= 6:
                        return True
                elif isinstance(x, str):
                    if x.isnumeric() and 0 <= int(x) <= 6:
                        return True
                    if x in Event.DAYS:
                        return True
                return False

            if isinstance(bday,str) and ',' in bday:
                bday = bday.split(',')
                bday = list(d.strip() for d in bday)

            if isinstance(bday,list):
                res = []
                for v in bday:
                    if not _valid(v):
                        continue

                    if str(v).isnumeric():
                        res.append(Event.DAYS[int(v)])
                        continue

                    res.append(v)

                if len(res) != 0:
                    return res

            elif _valid(bday):
                if str(bday).isnumeric():
                    return [Event.DAYS[int(bday)]]
                return [bday]


        cron = self.cron_data
        if cron is None:
            return None

        minute, hour, day, month, weekday = cron[0]

        if weekday != ["*"]:
            return list(Event.DAYS[int(w)] for w in weekday)

        return Event.DAYS

    @property
    @lru_cache
    def by_hour(self) -> list[int] | None:
        if self.is_all_day:
            return None

        data = self.data
        if "by-hour" in data:
            bhour = data['by-hour']

            def _valid(x) -> bool:
                if not str(x).isnumeric():
                    return False
                iv = int(x)
                return 0 <= iv <= 23

            if isinstance(bhour,str) and ',' in bhour:
                bhour = bhour.split(',')
                bhour = list(h.strip() for h in bhour)

            if isinstance(bhour,list):
                res = [int(v) for v in bhour if _valid(v)]
                if len(res) != 0:
                    return res

            elif _valid(bhour):
                return [int(bhour)]

        cron = self.cron_data
        if cron is None:
            return None

        minute, hour, day, month, weekday = cron[0]
        if hour != ["*"]:
            return [int(h) for h in hour]
        return list(range(0,24))

    @property
    @lru_cache
    def by_second(self) -> list[int] | None:
        if self.is_all_day:
            return None

        data = self.data
        if "by-second" in data:
            bsecond = data['by-second']

            def _valid(x) -> bool:
                return str(x).isnumeric() and 0 <= int(x) <= 59

            if isinstance(bsecond, str) and ',' in bsecond:
                bsecond = [s.strip() for s in bsecond.split(',')]

            if isinstance(bsecond, list):
                res = [int(v) for v in bsecond if _valid(v)]
                if res:
                    return res
            elif _valid(bsecond):
                return [int(bsecond)]

        return None

    @property
    @lru_cache
    def by_minute(self) -> list[int] | None:
        if self.is_all_day:
            return None

        data = self.data
        if "by-minute" in data:
            bminute = data['by-minute']

            def _valid(x) -> bool:
                return str(x).isnumeric() and 0 <= int(x) <= 59

            if isinstance(bminute, str) and ',' in bminute:
                bminute = [m.strip() for m in bminute.split(',')]

            if isinstance(bminute, list):
                res = [int(v) for v in bminute if _valid(v)]
                if res:
                    return res
            elif _valid(bminute):
                return [int(bminute)]

        cron = self.cron_data
        if cron is None:
            return None

        minute, hour, day, month, weekday = cron[0]
        if minute != ["*"]:
            return [int(m) for m in minute]

        return list(range(0, 60))

    @property
    @lru_cache
    def by_set_pos(self) -> list[int] | None:
        data = self.data

        if "by-set-pos" in data:
            bpos = data["by-set-pos"]

            def _valid(x) -> bool:
                # valores válidos: -366..-1 y 1..366 (según RFC5545)
                return str(x).lstrip("-").isnumeric() and -366 <= int(x) <= 366 and int(x) != 0

            if isinstance(bpos, str) and "," in bpos:
                bpos = [p.strip() for p in bpos.split(",")]

            if isinstance(bpos, list):
                res = [int(v) for v in bpos if _valid(v)]
                if res:
                    return res

            elif _valid(bpos):
                return [int(bpos)]

        return None

    @property
    @lru_cache
    def count(self) -> int | None:
        data = self.data
        if "count" in data:
            try:
                v = int(data["count"])
                return v if v > 0 else None
            except:
                return None
        return None

    @property
    @lru_cache
    def start(self) -> date | datetime | None:
        data  = self.data

        _date = data.get(
            'start',
            data.get("start-date", None )
        )

        if _date is None:
            return None

        if isinstance(_date,date):
            return _date

        if isinstance(_date,datetime):
            return _date

        if isinstance(_date,dict):
            y,m,d = _date.get('year'), _date.get("month"), _date.get("day")
            h,t,s = _date.get('hour'), _date.get("minute"), _date.get("second")
            _date = f"{y}-{m}-{d} {h}:{t}:{s}"

        if isinstance(_date,str):
            try:
                return parser.parse(_date)
            except Exception:
                return None

    @property
    @lru_cache
    def end(self) -> date | datetime | None:
        data  = self.data

        _date = data.get(
            'end',
            data.get("end-date", None )
        )

        if _date is None:
            return None

        if isinstance(_date,date):
            return _date

        if isinstance(_date,datetime):
            return _date

        if isinstance(_date,dict):
            y,m,d = _date.get('year'), _date.get("month"), _date.get("day")
            h,t,s = _date.get('hour'), _date.get("minute"), _date.get("second")
            _date = f"{y}-{m}-{d} {h}:{t}:{s}"

        if isinstance(_date,str):
            try:
                return parser.parse(_date)
            except Exception:
                return None


    @property
    @lru_cache
    def ics_content(self) -> str | None:
        # validations
        if  self.name is None \
         or self.start is None:
            return
        lines = []

        # start date should always be here
        _date = self.start
        if isinstance(_date,datetime) and self.is_all_day:
            _date = _date.date()
        if isinstance(_date,date):
            lines.append(f"DTSTART;VALUE=DATE:"+_date.strftime("%Y%m%d"))
            lines.append(f"DTSTAMP;VALUE=DATE:"+_date.strftime("%Y%m%d"))
        elif isinstance(_date, datetime):
            lines.append(f"DTSTART:"+_date.strftime("%Y%m%dT%H%M%S"))
            lines.append(f"DTSTAMP:"+_date.strftime("%Y%m%dT%H%M%S"))


        if self.end:
            _date = self.end

            if isinstance(_date, datetime) and self.is_all_day:
                _date = _date.date()
            if isinstance(_date, date):
                lines.append(f"DTEND;VALUE=DATE:{_date.strftime('%Y%m%d')}")
            elif isinstance(_date, datetime):
                lines.append(f"DTEND:{_date.strftime('%Y%m%dT%H%M%S')}")



        if self.frequency:
            rrule = f"RRULE:FREQ={self.frequency}"

            if self.interval:
                rrule += f";INTERVAL={self.interval}"
            if self.by_month:
                months = ",".join( str(m) for m in self.by_month)
                rrule += f";BYMONTH={months}"
            if self.by_month_day:
                days = ",".join(str(d) for d in self.by_month_day )
                rrule += f";BYMONTHDAY={days}"
            if self.by_day:
                wday = ",".join(d for d in self.by_day)
                rrule += f";BYDAY={wday}"
            if self.by_set_pos:
                spos = ",".join(str(d) for d in self.by_set_pos)
                rrule += f";BYSETPOS={spos}"
            if self.by_hour:
                hours = ",".join(str(h) for h in self.by_hour)
                rrule += f";BYHOUR={hours}"
            if self.by_minute:
                mins = ",".join(str(m) for m in self.by_minute)
                rrule += f";BYMINUTE={mins}"
            if self.by_second:
                secs = ",".join(str(m) for m in self.by_second)
                rrule += f";BYSECOND={secs}"
            if self.count:
                rrule += f";COUNT={self.count}"


            lines.append(rrule)


        if self.description:
            desc = self.description.replace(
                           "\\", "\\\\"
               ).replace(  ";", r"\;"
               ).replace(  ",", r"\,"
               ).replace(  "\n", r"\n"
            )

            lines.append(f"DESCRIPTION:{desc}")

        if self.priority:
            lines.append(f"PRIORITY:{self.priority}")


        if len(lines) != 0:
            lines = [
                "BEGIN:VEVENT",
                f"UID:{self.uid}",
                f"SUMMARY:{self.name}",
                *lines,
                "END:VEVENT"
            ]

            return "\n".join(lines)

        return None
