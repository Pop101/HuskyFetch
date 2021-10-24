from typing import NamedTuple


class Event(NamedTuple):
    name: str
    description: str
    location: str
    start_time: int
    end_time: int


class Scraper():
    def __init__(self) -> None:
        #raise NotImplementedError('Scraper must be implemented')
        # Scaper must be implemented
        pass

    async def scrape(self) -> list:
        import datetime
        now = int(datetime.datetime.utcnow().timestamp())
        print('abcde')
        print(now)
        return [
            Event(name='TestVent', description='example event',
                  location='CSE2', start_time=now, end_time=now + 3600),
            Event('DubHax', 'You right now', 'here', now-3600, now+3600)
        ]
