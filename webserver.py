from datetime import datetime, timedelta
from os import path
from flask import Flask, render_template, request
from waitress import serve
from modules.scraper import get_all_classes
import pickle

from apscheduler.schedulers.background import BackgroundScheduler

DATABASE_PATH = "database.pk"
UPDATE_INTERVAL = 3600

app = Flask(__name__)

counter = 0


@app.route("/", methods=["GET"])
def render_index():
    return render_template("index.html", counter=counter)


@app.route("/api/locateEvents", methods=["GET"])
def locate_events():
    timespan = request.args.get("span", default=2 * 3600, type=float)
    timespan = timedelta(seconds=timespan)

    def course_to_dict(course):
        now = datetime.now()
        closest_timeframe = min(course.timeframes, key=lambda x: (x.start > now, abs(x.start - now)))
        return {
            "name": course.name,
            "description": course.description,
            "location": course.location,
            "capacity": course.capacity,
            "start_time": datetime.timestamp(closest_timeframe.start),
            "end_time": datetime.timestamp(closest_timeframe.end),
        }

    global counter
    counter += 1
    return {
        "courses": [course_to_dict(course) for course in get_valid_events(timespan)],
    }


def get_valid_events(max_time_until_start: timedelta = timedelta(hours=2)):
    events = load_database()["events"]
    for event in events:
        if not event.capacity:
            continue
        if int(event.capacity[1]) <= 80:
            continue

        for timeframe in event:
            now = datetime.now()
            if now < timeframe.start < now + max_time_until_start:
                yield event


def load_database():
    if not path.exists(DATABASE_PATH):
        return update_database()

    with open(DATABASE_PATH, "rb") as f:
        db = pickle.load(f)

    if db["last_updated"] + UPDATE_INTERVAL < datetime.now().timestamp():
        return update_database()
    return db


def update_database():
    events = list()
    for cls in get_all_classes():
        events.append(cls)

    prog_info = {
        "last_updated": datetime.now().timestamp(),
        "events": events,
    }
    with open(DATABASE_PATH, "wb") as f:
        pickle.dump(prog_info, f)
    return prog_info


load_database()
print("initial scraping complete")

scheduler = BackgroundScheduler()
scheduler.add_job(update_database, "interval", seconds=UPDATE_INTERVAL)
scheduler.start()

print("Serving on port 7575")
serve(app, host="0.0.0.0", port=7575)
