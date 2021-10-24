from selenium import webdriver

from datetime import datetime
from dateutil import parser

import selenium
from .abstract_scraper import Scraper, Event


class HuskyLinkScraper(Scraper):
    async def scrape(self, seleniumdriver: selenium.webdriver = None) -> list:
        driver = webdriver.PhantomJS() if not seleniumdriver else seleniumdriver
        driver.get('https://huskylink.washington.edu/events')

        events = []
        for elem in driver.find_elements_by_xpath('//*[@id="event-discovery-list"]/div/*'):
            name = elem.text.split('\n')[0]
            date = elem.text.split('\n')[1]
            location = elem.text.split('\n')[2]
            organizers = elem.text.split('\n')[3]

            print(name, date, location, organizers)

            date = self.parse_date(date)

            # Go to the page for the event
            event_link = elem.find_element_by_xpath(
                './/a').get_attribute('href')

            # switch to new tab to get event data
            driver.execute_script("window.open('about:blank', 'tab2');")
            driver.switch_to_window("tab2")
            driver.get(event_link)
            enddate = driver.find_element_by_xpath(
                # '//div[@role="main"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/p[2]'
                '//strong/../div[2]/p[2]')
            enddate = self.parse_date(enddate.text)

            description = driver.find_element_by_xpath('//h2/../div')
            description = description.text

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            # Create event
            event = Event(name, location, description + '\nHosted by ' + organizers.title(),
                          int(date.timestamp()), int(enddate.timestamp()))
            events.append(event)

        if not seleniumdriver:
            driver.quit()
        return events

    def parse_date(self, date: str) -> datetime:
        parsed_date = parser.parse(date)
        if not parsed_date.tzinfo:
            parsed_date.replace(tzinfo=parsed_date.now().tzinfo)
        return parsed_date
