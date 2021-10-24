from .abstract_scraper import Scraper, Event

import re
from datetime import datetime, date, time, timedelta

from selenium import webdriver

debug = False


class ClassScraper(Scraper):
    QUARTER_CENTERS = {
        'WIN': date(month=1, day=1, year=1) + timedelta(weeks=5),
        'SPR': date(month=3, day=28, year=1) + timedelta(weeks=5),
        'SUM': date(month=6, day=21, year=1) + timedelta(weeks=5),
        'AUT': date(month=9, day=29, year=1) + timedelta(weeks=5),
    }

    async def scrape(self, seleniumdriver: webdriver = None) -> list:
        now = datetime.now().replace(
            year=list(ClassScraper.QUARTER_CENTERS.values())[0].year
        )

        current_quarter = min(ClassScraper.QUARTER_CENTERS.items(),
                              key=lambda center: abs(
                                  (center[1]-now.date()).days)
                              )
        if abs((current_quarter[1]-now.date()).days) > 5*7:
            print('It\'s not class season')
            return []

        driver = webdriver.PhantomJS() if not seleniumdriver else seleniumdriver
        driver.get(
            f'https://www.washington.edu/students/timeschd/{current_quarter[0]}{datetime.now().year}/'
        )

        # record all links
        print('recording links')
        links_to_site = list()
        for elem in driver.find_elements_by_xpath('//div[contains(@class, "uw-body")]//ul//a[contains(@href,".html")]')[1:]:
            links_to_site.append(elem.get_attribute('href'))

        events = list()
        for link in links_to_site:
            try:
                events.extend(self.parse_timeschd(link, driver))
            except Exception as e:
                if debug:
                    raise e
                continue
        return events

    def parse_timeschd(self, page: str, driver: webdriver):
        if not 'www.washington.edu/students/timeschd' in page:
            return

        driver.get(page)
        crscat_links = set()
        classes_by_id = dict()
        for cls in driver.find_elements_by_xpath('//table//pre/a/..'):
            # TODO: parse classes with dates on multiple lines
            # https://www.washington.edu/students/timeschd/AUT2021/math.html
            if not '/' in cls.text:
                continue
            txt = cls.text.replace('\t', '   ')
            # print(txt)
            # print(txt[38:48])

            max_people = txt[txt.rfind('/'):]
            max_people = max_people[1:min(10, len(max_people))].strip()

            # only allow large classes
            # TODO: don't fill up seats if class is 95% full
            try:
                if int(max_people) < 70:
                    continue
            except ValueError as e:
                if debug:
                    raise e
                continue

            course_times = list()
            for line in txt.split('\n'):
                try:
                    if 'remote' in line:
                        continue
                    days = line[24:31].strip()
                    if 'arrange' in days.lower():
                        continue
                    if 'tba' in days.lower():
                        continue

                    days = [ClassScraper.get_nearest_weekday(
                        day) for day in re.findall(r'[A-Z][^A-Z]*', days)]
                    days = list(filter(lambda day: day != None, days))

                    time = line[31:41].strip()
                    # Issue: time is formatted extremely strangely
                    # Classes run from 6:30-8:00, so we cannot assume am or pm
                    # sadly, pm times are listed as 630-800, ambiguous
                    # times like 9:30-10:00 are not ambiguous
                    # therefore, we ignore all times before 1200 and assume pm
                    start, end = time.split('-')
                    start_hrs = int(start[:-2])
                    end_hrs = int(end[:-2])
                    if 6 <= start_hrs < 10 and end_hrs < 10:
                        continue  # ambiguous when there's no third digit

                    if end_hrs < start_hrs:
                        end_hrs += 12

                    start_mins = int(start[-2:])
                    end_mins = int(end[-2:])

                    # Logically, if each day can have a different time,
                    # they can have a different location too

                    for day in days:
                        # clone day timestamp
                        start_time = day.replace(
                            hour=start_hrs, minute=start_mins)
                        end_time = day.replace(hour=end_hrs, minute=end_mins)

                        for week in range(0, 1):
                            course_times.append(
                                (start_time + timedelta(days=7*week), end_time +
                                 timedelta(days=7*week), line[40:56].strip())
                            )
                except Exception as e:
                    if debug:
                        raise e
                    else:
                        continue
            #print('COURSETIMES--', course_times)

            # get table header
            header = cls.find_element_by_xpath(
                './../../../../preceding-sibling::table[position() < 2]//a[contains(@href,".html")]'
            )

            link_to = header.get_attribute('href')

            class_name_id = str(link_to)[str(link_to).rfind('#')+1:]
            if '#' in link_to:
                link_to = link_to[:link_to.find('#')]

            crscat_links.add(link_to)
            classes_by_id[class_name_id] = [
                Event(
                    name=class_name_id,
                    description='TODO+name',
                    location=location,
                    start_time=start_time.timestamp(),
                    end_time=end_time.timestamp()
                )
                for start_time, end_time, location in course_times
            ]
            #print('EVENTS-WITHOUT-DESCR---', classes_by_id[class_name_id])

        # Gather all descriptions and titles
        #print('CRSCATLNKS----', crscat_links)
        events = list()
        for crscat_link in crscat_links:
            driver.get(crscat_link)
            for class_id, event_list in list(classes_by_id.items()):
                # Search for element of class_id in the page

                try:
                    description_block = driver.find_element_by_xpath(
                        f'//p//*[@name="{class_id}"]')
                except:
                    continue

                description = description_block.text.split('\n')[1:]
                title = description_block.text.split('\n')[0]
                if '(' in title:
                    title = title[:title.find('(')]

                # Replace each event's title and description with the corrected ones
                new_event_list = list()
                for event in event_list:
                    new_event_list.append(
                        Event(name=title,
                              description='\n'.join(description),
                              location=event.location,
                              start_time=int(event.start_time),
                              end_time=int(event.end_time))
                    )

                # Add each event to the class list
                events.extend(new_event_list)
                classes_by_id.pop(class_id)

                # print('------description--------')
                #print(title, description)
        return events

    @ staticmethod
    def get_nearest_weekday(day: str) -> datetime:
        # parse day to weekday
        day = day.title()
        if day.startswith('M'):
            day = 0
        elif day.startswith('Th'):
            day = 3
        elif day.startswith('T'):
            day = 1
        elif day.startswith('W'):
            day = 2
        elif day.startswith('F'):
            day = 4
        elif day.startswith('S'):
            day = 5
        else:
            return None  # given weekday isn't valid

        now = datetime.now()
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now.weekday() < day:
            now += timedelta(days=day-now.weekday())
        else:
            now += timedelta(days=7-now.weekday()+day)

        return now


if __name__ == '__main__':
    print(ClassScraper.get_nearest_weekday('M'))
