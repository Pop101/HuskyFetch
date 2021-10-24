from datetime import datetime, timedelta
import requests
from flask import Flask, render_template
import selenium
from waitress import serve
from modules import scrapers

import json
from Levenshtein import distance

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from apscheduler.schedulers.background import BackgroundScheduler

import asyncio
app = Flask(__name__)

counter = 0

scrapers = {
    'events': [scrapers.HuskyLinkScraper(), scrapers.UWCalendar_Scraper()],
    'classes': [scrapers.ClassScraper()],
    'bustling': [scrapers.GoogleMapsScraper()]
}


@app.route('/', methods=['GET'])
def render_index():
    return render_template('index.html', counter=counter)


@app.route('/api/locateEvents', methods=['GET'])
def locate_events():
    responses = get_recent_events()

    global counter
    counter += 1
    return responses


def get_recent_events(max_time_until_start: int = 40*60*1000, max_time_until_end: int = 1000*5*3600):
    results = {}
    with open('database.json') as f:
        results = json.loads(f.read())

    now = datetime.now().timestamp() + timedelta(days=2, hours=4).total_seconds()
    for type in results.keys():
        results[type] = [
            event for event in results[type]
            if 0 < event['start_time'] - now < max_time_until_start and
            event['end_time'] - now < max_time_until_end
        ]
    return results


def update_database():
    # grab results from scrape_all
    results = asyncio.run(scrape_all())

    # parse all events to dictionary
    for type in results.keys():
        results[type] = [
            event._asdict() for event in results[type]
        ]

    # scan all events for similar events and remove those that are similarly named
    new_results = {}
    for type in results.keys():
        new_results[type] = []
        for event in results[type]:
            is_similar = False
            for existing_event in new_results[type]:
                # If less than 10% different, remove the existing event
                if distance(event['name'], existing_event['name']) < 0.1*max(len(event['name']), len(existing_event['name'])):
                    is_similar = True
                    break
            if not is_similar:
                new_results[type].append(event)

            # save to file
    with open('database.json', 'w') as f:
        f.write(json.dumps(new_results))
        print('Database updated')


async def scrape_all():
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox")  # linux only
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    responses = {}
    for type in scrapers.keys():
        for scraper in scrapers[type]:
            if type not in responses:
                responses[type] = list()
            print('Beginning scrape of', type)
            responses[type].extend(await scraper.scrape(seleniumdriver=driver))

    driver.quit()
    print('Scrape complete')
    return responses


# update_database()
print('initial scraping complete')

scheduler = BackgroundScheduler()
scheduler.add_job(update_database, 'interval', hours=2)
scheduler.start()

serve(app, host='0.0.0.0', port=8080)
#app.run(host='0.0.0.0', port=8080)
