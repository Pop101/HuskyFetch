
# big thanks to https://github.com/mrmorais/behavior-map-natal/blob/master

from .abstract_scraper import Scraper, Event
from datetime import datetime
import time
import random
import requests
import livepopulartimes

from selenium import webdriver

with open('googlemaps_key.txt') as f:
    API_KEY = f.read()
assert API_KEY and 'APIKEY' not in API_KEY, 'API_KEY not found'

PLACE_TYPES = ['cafe', 'restaurant',
               'library', 'gym', 'shopping_mall', 'store', 'library', 'park']

FOUNTAIN_LOCATION = ['47.65373', '-122.3077']


# radius is in meters
def get_nearby_places(location: str, types: list, pages: int or None = None, radius: int = 2000):
    if ',' not in location:
        raise ValueError('location must be of format lat,long (ex: 20,-42)')

    if pages == None:
        pages = 1

    results = list()
    next_page_url = None

    for page_num in range(pages):
        if page_num == 0:
            resp = requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json', params={
                'location': location,  # "latitude,longitude" -> "144,20"
                'radius': radius,
                'type': types,
                'key': API_KEY
            })
            resp.raise_for_status()
            resp = resp.json()
        else:
            resp = requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json', params={
                'pagetoken': next_page_url,
                'key': API_KEY
            })
            resp.raise_for_status()
            resp = resp.json()

        results.extend(resp['results'])

        if 'next_page_token' in resp:
            next_page_url = resp['next_page_token']
        else:
            break

        time.sleep(1)
    return results


def is_busy(place_info: dict):
    # must be open right now

    if 'opening_hours' in place_info and not place_info['opening_hours']['open_now']:
        # return 0
        pass

    popularity_info = livepopulartimes.get_populartimes_by_PlaceID(
        API_KEY, place_info['place_id'])

    if popularity_info['current_popularity']:
        if isinstance(popularity_info['current_popularity'], str):
            if 'no wait' not in popularity_info['current_popularity'].lower():
                return 1, popularity_info
            elif 'wait' in popularity_info['current_popularity'].lower():
                return 2, popularity_info
        elif isinstance(popularity_info['current_popularity'], int):
            val = popularity_info['current_popularity']
            print('popularity score:', val)
            if val < 15:
                return 1, popularity_info
            elif val < 30:
                return 2, popularity_info
            else:
                return 3, popularity_info

    return 0, popularity_info


class GoogleMapsScraper(Scraper):
    def __init__(self) -> None:
        self.locations = get_nearby_places(
            ','.join(FOUNTAIN_LOCATION), PLACE_TYPES, 2)

    async def scrape(self, seleniumdriver: webdriver = None) -> list:
        # Loop over all locations and get if they're busy. If they are, simply add them as events

        events = list()
        for location in self.locations:
            name = location['name']
            address = location['vicinity']
            lvl, pop = is_busy(location)

            if lvl:
                events.append(Event(
                    name=name,
                    description=str(pop['current_popularity']).title() if pop['current_popularity'] else random.choice(
                        ['Unusually busy', ' Quite a bustle going on there']),
                    location=address,
                    start_time=int(datetime.now().timestamp() + 3*60),
                    end_time=int(datetime.now().timestamp() + lvl*3600)
                ))
        return events


if __name__ == '__main__':
    places = get_nearby_places(','.join(FOUNTAIN_LOCATION), PLACE_TYPES, 2)

    print(places)
    print(is_busy(places[0]))
