from .huskylink_scraper import HuskyLinkScraper
from .class_scraper import ClassScraper
from .uwcalendar_scraper import UWCalendar_Scraper
from .google_maps_scraper import GoogleMapsScraper
from .abstract_scraper import Scraper


# Test it
if __name__ == '__main__':
    from selenium import webdriver
    #driver = webdriver.Chrome()
    driver = None
    scraper = GoogleMapsScraper()
    import asyncio
    feet = asyncio.run(scraper.scrape(seleniumdriver=driver))
    print(feet)
