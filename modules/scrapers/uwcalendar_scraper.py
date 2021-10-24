from .abstract_scraper import Scraper, Event
import requests
import icalendar
from selenium import webdriver

from datetime import datetime, time

DateType = type(datetime.now().date())


class UWCalendar_Scraper(Scraper):
    async def scrape(self, seleniumdriver: webdriver = None) -> list:
        response = requests.get(
            'https://www.trumba.com/calendars/sea_campus.ics?filterview=No+Ongoing+Events&filter5=_409198_&filterfield5=30051')
        cal = icalendar.Calendar.from_ical(response.content)
        events = []
        for event in cal.walk('vevent'):
            try:
                title = str(event.get('summary')).replace(
                    'Deadline to', '').replace('EXHIBIT:', '').strip()
                location = str(event.get('location'))
                start = event.get('dtstart').dt
                end = event.get('dtend').dt
            except:
                continue

            # ignore online events
            if 'online' in f'{title}{location}'.lower():
                continue
            if 'zoom' in f'{location}'.lower():
                continue
            if 'none' in location.lower():
                location = ''

            if isinstance(start, DateType):
                start = datetime.combine(start, time(
                    hour=8, tzinfo=datetime.now().tzinfo))
            if isinstance(end, DateType):
                end = datetime.combine(end, time(
                    hour=22, tzinfo=datetime.now().tzinfo))
            events.append(Event(title, '', location, int(
                start.timestamp()), int(end.timestamp())))
        return events
