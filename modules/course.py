from dateutil import parser
from datetime import datetime, date, timedelta, time
from timeframe import TimeFrame


class Course:
    # Stores information about a course
    # Name, description
    # Capacity
    # Location (room + building)
    # Times (day, time, duration)
    def __init__(self, name: str = None, descr: str = None, loc: str = None, cap: tuple = None) -> None:
        self.set_info(name, descr, loc, cap)
        self.days = None
        self.start_date = None
        self.end_date = None
        self.start_time = None
        self.end_time = None
        self.timeframes = list()

    def set_info(self, name: str = None, descr: str = None, loc: str = None, cap: tuple = None) -> None:
        self.name = name
        self.description = descr
        self.location = loc
        self.capacity = cap

    def set_days(self, days: list) -> None:
        self.days = days
        self.recalculate_timeframe()

    def set_dates(self, start_date: date, end_date: date) -> None:
        self.start_date = start_date
        self.end_date = end_date

        self.recalculate_timeframe()

    def set_time(self, start_time: time, end_time: time) -> None:
        self.start_time = start_time
        self.end_time = end_time

        self.recalculate_timeframe()

    def recalculate_timeframe(self) -> None:
        self.timeframes = list()
        if not self:
            return

        # Loop between start and end date
        date = self.start_date
        while date <= self.end_date:
            if date.weekday() in self.days:
                start = datetime.combine(date, self.start_time)
                end = datetime.combine(date, self.end_time)
                frame = TimeFrame(start, end)
                self.timeframes.append(frame)

            date += timedelta(days=1)

    def __bool__(self) -> bool:
        return bool(self.name and self.days and self.start_date and self.end_date and self.start_time and self.end_time)

    def __str__(self) -> str:
        occurances = len(self.timeframes) if self.timeframes else 0
        cap_str = f"{self.capacity[0]}/{self.capacity[1]}" if self.capacity else "N/A"
        return f'<Course "{self.name}", {occurances} scheduled at {self.location}. {cap_str} ppl>'

    def __iter__(self) -> TimeFrame:
        self.recalculate_timeframe()
        for frame in self.timeframes:
            yield frame

    def __getstate__(self) -> dict:
        del self.timeframes
        return self.__dict__

    def __setstate__(self, d) -> None:
        self.__dict__ = d
        self.recalculate_timeframe()


if __name__ == "__main__":
    crs = Course("Test Course", "Test Description", "Test Location", (1, 2))
    print(crs)
    crs.set_dates(date(2022, 1, 1), date(2022, 1, 31))
    crs.set_days([0])
    crs.set_time(parser.parse("8:00").time(), parser.parse("9:00").time())
    print(crs.__dict__)
    print("\n\n", crs)
