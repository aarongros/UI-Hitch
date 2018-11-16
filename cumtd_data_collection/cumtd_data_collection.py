# -*- coding: utf-8 -*-
"""cumtd_data_collection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14Krwjwsa7aOzDDyhMeFuwxXwvJJxb4ro
"""

### IMPORTS AND DEFINED CONSTANTS ###

import requests
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
#import __builtin__
import time, re, os

from apikey import keys
VERSION = "v2.2"
OUTPUT_FORMAT = "json"
API_KEY = keys['CUMTD']

os.environ['TZ'] = 'America/Chicago'
time.tzset()

DB_NAMES = ['stop_times', 'unscheduled_stops']
DB_FILE = 'stop_times.db'

# see debug() comments for levels
# any value > 3 will print nothing
DEBUG_LEVEL = 3
TRIPS = None
STOPS = None
STOP_TIMES_ALL = None # csv's that will be read in later

### HELPER FUNCTIONS ###

class HourlyRequestLimitReached(Exception): pass
class FileNotFoundException(Exception): pass

def cumtd_request_url(methodname, other_args={}, version=VERSION, output=OUTPUT_FORMAT, key=API_KEY):
	rooturl = "https://developer.cumtd.com/api/{v}/{f}/".format(v=VERSION, f=OUTPUT_FORMAT)
	url = rooturl + methodname + "?key={}".format(key)
	for param, value in other_args.items():
		url = url + "&{}={}".format(param, value)
	return url


# arrange into csv
def generate_all_stops_csv(filename):
    if filename in os.listdir(): 
        debug("INIT", "found '{}', continuing".format(filename), 1)
        return
    
    debug("INIT", "didn't find '{}', creating new".format(filename), 1)
    
    r = requests.get(cumtd_request_url("getstops"))
    json = r.json()
	
    stops = {'stop_id': [], 
           'stop_name': [], 
           'code': [], 
           'distance': [], 
           'specific_stop_code': [], 
           'specific_stop_stop_id': [], 
           'specific_stop_stop_lat': [], 
           'specific_stop_stop_lon': [], 
           'specific_stop_stop_name': []}

    for stop in json['stops']:
        for key in stop.keys():
            if key in ['stop_id', 'stop_name', 'code', 'distance']:
                stops[key].append(stop[key])
            elif key == 'stop_points': pass
        for key in ['specific_stop_code', 
                'specific_stop_stop_id', 
                'specific_stop_stop_lat', 
                'specific_stop_stop_lon', 
                'specific_stop_stop_name']:
            stops[key].append('')
        for specific_stop in stop['stop_points']:
            for key in specific_stop.keys():
                if key in ['code', 'stop_id', 'stop_lat', 'stop_lon', 'stop_name']:
                    stops['specific_stop_' + key].append(specific_stop[key])
            for key in ['stop_id', 'stop_name', 'code', 'distance']:
                stops[key].append('')

    pd.DataFrame(stops).to_csv(filename, index=False)
	

def name_to_stop_id(name):
	if name in list(STOP_TIMES_ALL['stop_name']):
		return STOP_TIMES_ALL[STOP_TIMES_ALL['stop_name'] == name].iloc[0]['stop_id']
	elif name in list(STOP_TIMES_ALL['specific_stop_stop_name']):
		return STOP_TIMES_ALL[STOP_TIMES_ALL['specific_stop_stop_name'] == name]\
            .iloc[0]['specific_stop_stop_id']
	else:
		return None
    
def trip_id_to_route_id(trip_id):
    return TRIPS.loc[TRIPS['trip_id'].tolist().index(trip_id)]['route_id']
	

def cumtd_csv_to_sqlite(sqlite_file):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    # if the table/database exists, then don't create one
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{}';"\
              .format(DB_NAMES[0]))
    if c.fetchone()[0] != 0: 
        debug("INIT", "'{}' table exists, moving on".format(DB_NAMES[0]), 1)
    else:
        debug("INIT", "creating table '{}' because didn't find one"\
              .format(DB_NAMES[0]), 1)

        create_table_str = "CREATE TABLE IF NOT EXISTS {} (".format(DB_NAMES[0])+\
            'trip_id VARCHAR(60) NOT NULL,'+\
            'arrival_time VARCHAR(8) NOT NULL,'+\
            'stop_id VARCHAR(17) NOT NULL,'+\
            'stop_sequence INTEGER,'+\
            'route_id VARCHAR NOT NULL,'+\
            "PRIMARY KEY('trip_id', 'arrival_time'));"
        c.execute(create_table_str)

        for row in STOPS.iterrows():
            cmd_str = "INSERT OR IGNORE INTO stop_times("+\
                "trip_id,arrival_time,stop_id,stop_sequence,route_id) VALUES ("
            trip_id = row[1]['trip_id']
            arrival_time = row[1]['arrival_time']
            stop_id = row[1]['stop_id']
            stop_sequence = row[1]['stop_sequence']
            route_id = trip_id_to_route_id(row[1]['trip_id'])
            arrival_id = trip_id + " " + arrival_time # unique arrival identifier
            cmd_str += "'{}', '{}', '{}', {}, '{}')".format(
                trip_id,arrival_time,stop_id,stop_sequence,route_id)
            c.execute(cmd_str)
        debug("INIT", "created table '{}'".format(DB_NAMES[0]), 1)

    # check if this table exists too
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{}';"\
              .format(DB_NAMES[1]))
    if c.fetchone()[0] != 0: 
        debug("INIT", "'{}' table exists, moving on".format(DB_NAMES[1]), 1)
    else:
        debug("INIT", "creating table '{}' because didn't find one"\
              .format(DB_NAMES[1]), 1)

        create_table_str = "CREATE TABLE IF NOT EXISTS {} (".format(DB_NAMES[1])+\
            'arrival_date DATE NOT NULL,'+\
            'arrival_time VARCHAR(8) NOT NULL,'+\
#            'trip_id VARCHAR NOT NULL,'+\
            'delay INTEGER);'
        c.execute(create_table_str)
        debug("INIT", "created table '{}'".format(DB_NAMES[1]), 1)
	
    conn.commit()
    conn.close()
    
def debug(flag, msg, importance):
    # importance:
    # 3 - errors, starts/stops
    # 2 - unexpected but handled events
    # 1 - business as normal, everything else
    if importance >= DEBUG_LEVEL:
        print("[{}] {}: {}".format(flag, datetime.now(), msg))

### LOGGING/UPDATING FUNCTIONS ###

def update_db(arrival_date, diff, trip_id, arrival_time, scheduled):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if scheduled:
        new_row = True
        for row in c.execute("PRAGMA table_info('{}')".format(DB_NAMES[0])):
            if row[1] == arrival_date:
                new_row = False
        if new_row:
            c.execute("ALTER TABLE {} ADD '{}' INTEGER".format(
                DB_NAMES[0], arrival_date))
            debug("UPDATE_DB","new column created: {}".format(arrival_date),1)

        exec_str = "UPDATE {} SET '{}' = {} WHERE trip_id LIKE '{}' AND arrival_time LIKE '{}';"\
                .format(DB_NAMES[0], arrival_date, diff, trip_id, arrival_time)
        c.execute(exec_str)
    else:
        exec_str = "INSERT INTO {} (".format(DB_NAMES[1])+\
            "arrival_date,arrival_time,trip_id,delay"+\
            ") VALUES ('{}','{}',{});".format(arrival_date,\
            arrival_time, diff)
        c.execute(exec_str)
        debug("UNSCHEDULED","unscheduled stop added",2)
        
    conn.commit()
    conn.close()


def parse_store_cumtd_data(input, result):
    if 'departures' not in result:
        if result['status']['code'] == 403:
            # request limit per hour reached, don't request anymore
            debug("ERROR", "request limit per hour reached, halting collection", 3)
            raise HourlyRequestLimitReached("request limit per hour reached")
        elif result['status']['code'] == 404:
            # bus doesn't exist (for that hour?) - ignore
            debug("ERROR", "'{}' not found".format(input), 2)
            return False
        else:
            debug("ERROR", "input: '{}' returned: {}"\
                  .format(input, result['status']['msg']), 3)
            return False
    else:
        departures_logged = 0
        for departure in result['departures']:
            scheduled = departure['is_scheduled']
            if scheduled: trip_id = departure['trip']['trip_id']
            else: trip_id = None
            scheduled_time = datetime.strptime(
                departure['scheduled'], "%Y-%m-%dT%H:%M:%S-06:00")
            diff = int((datetime.strptime(
                departure['expected'], "%Y-%m-%dT%H:%M:%S-06:00")
                - scheduled_time).total_seconds())
            arrival_date, arrival_time = str(scheduled_time).split(' ')
            if scheduled_time.hour <= 6:
                arrival_date = str(scheduled_time - timedelta(1,0))[:10]
                arrival_time = str(int(arrival_time[:2]) + 24) + arrival_time[2:]
            update_db(arrival_date, diff, trip_id, arrival_time,  scheduled)
            departures_logged += 1
        debug("STORE_DATA", 
              "finished logging {}: {} departures logged".format(
                  result['rqst']['params']['stop_id'].upper(), 
                  departures_logged),2)    
        return True


def has_stops(stop_id, minutes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for stop in c.execute("SELECT arrival_time FROM {} ".format(DB_NAMES[0])+\
            "WHERE stop_id LIKE '{0}:%' OR stop_id LIKE '{0}' ".format(stop_id)+\
            "ORDER BY arrival_time"):
        other_time = [int(x) for x in stop[0].split(":")]
        if other_time[0] > 23: other_time[0] -= 24
        now_time = datetime.now().time()
        if timedelta(minutes=0) < \
            timedelta(hours=other_time[0], 
                      minutes=other_time[1], 
                      seconds=other_time[2]) \
            - timedelta(hours=now_time.hour, 
                        minutes=now_time.minute, 
                        seconds=now_time.second) \
            < timedelta(minutes=minutes):
            conn.close()
            debug("HAS_STOPS", "{} has a stop within next {} minutes".format(
					stop_id, minutes), 1)
            return True
    debug("HAS_STOPS", "{} does not have a stop within next {} minutes".format(
            stop_id, minutes), 1)
    conn.close()
    return False

def collect_available_stops(stops, minutes_between):
    has_stops_list = list(filter(lambda x : has_stops(x, minutes_between), stops))
    return has_stops_list

def analyze_all_stops(stops, minutes_between = 60, sleep_time = 3):
    start = datetime.now()
    stops_requested = 0
    continue_collecting = True
    for stop_id in stops:
        if continue_collecting:
            try:
                r = requests.get(cumtd_request_url("getdeparturesbystop", 
                    {'stop_id': stop_id, 'pt': minutes_between}))
                success = parse_store_cumtd_data(stop_id, r.json())
                if success: 
                    stops_requested += 1
                    time.sleep(sleep_time)
            except requests.exceptions.ConnectionError as e:
                debug("ERROR", "ConnectionError: {}".format(str(e)), 3)
            except HourlyRequestLimitReached as e:
                continue_collecting = False
    return (stops_requested, datetime.now() - start)

### MAIN WRAPPER FUNCTIONS ###

def setup():
    # read in csv's
    if 'google_transit' not in os.listdir():
        debug("ERROR", "cannot find 'google_transit' folder", 3)
        raise FileNotFoundException('google_transit')
    
    global TRIPS
    TRIPS = pd.read_csv('google_transit/trips.txt')
    global STOPS
    STOPS = pd.read_csv('google_transit/stop_times.txt')
    
	# run once per folder
    generate_all_stops_csv('all_stops.csv')
    global STOP_TIMES_ALL
    STOP_TIMES_ALL = pd.read_csv('all_stops.csv')
    
	# initial creation of database
    cumtd_csv_to_sqlite('stop_times.db')
    


def main(start_immediately = True):
    minutes_between = 60

    all_stops = STOPS.loc[:]['stop_id']
    stops = set([x[:-2] if x != '' and re.match(".+:[0-9]{1}", x) else x 
                 for x in all_stops])
    stops = sorted(stops)

    delay_between_queries = 0

    # main loop
    while True:
        if start_immediately:
            debug("STARTING", "Starting data collection", 3)
            start = datetime.now()
            available_stops = collect_available_stops(stops, minutes_between)
            debug("COLLECTING", "{} stops have a departure in the next {} minutes: took: {}"\
                    .format(len(available_stops), minutes_between, datetime.now() - start), 3)
            stops_analyzed, time_taken = \
                analyze_all_stops(available_stops, minutes_between, delay_between_queries)
            debug("FINISHING", "Finished collecting data for {} stops in time: {}".format(
                stops_analyzed, time_taken), 3)
        else: 
            start_immediately = True
            time_taken = timedelta(seconds=0)

        if time_taken < timedelta(minutes=minutes_between):
            debug("WAITING", "waiting until next hour", 3)
            time.sleep(60)
            while datetime.now().time().minute > 1:
                time.sleep(60)
        else:
            debug("WAITING", "not waiting because last round took over {} minutes"\
                  .format(minutes_between), 3)

setup()
main(False)
