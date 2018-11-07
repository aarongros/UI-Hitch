import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import time, re

from apikey import keys #outside actual git repo, make sure to add file/replace with own apikey
VERSION = "v2.2"
OUTPUT_FORMAT = "json"
API_KEY = keys['CUMTD']

def cumtdRequestUrl(methodname, other_args={}, version=VERSION, output=OUTPUT_FORMAT, key=API_KEY):
    rooturl = "https://developer.cumtd.com/api/{v}/{f}/".format(v=VERSION, f=OUTPUT_FORMAT)
    url = rooturl + methodname + "?key={}".format(key)
    for param, value in other_args.items():
        url = url + "&{}={}".format(param, value)
    return url


# arrange into csv
def generateAllStopsCsv(filename):
    r = requests.get(cumtdRequestUrl("getstops"))
    json = r.json()
    
    stops = {'stop_id': [], 'stop_name': [], 'code': [], 'distance': [], 'specific_stop_code': [], 'specific_stop_stop_id': [], 'specific_stop_stop_lat': [], 'specific_stop_stop_lon': [], 'specific_stop_stop_name': []}

    for stop in json['stops']:
        for key in stop.keys():
            if key in ['stop_id', 'stop_name', 'code', 'distance']:
                stops[key].append(stop[key])
            elif key == 'stop_points': pass
        for key in ['specific_stop_code', 'specific_stop_stop_id', 'specific_stop_stop_lat', 'specific_stop_stop_lon', 'specific_stop_stop_name']:
            stops[key].append('')
        for specific_stop in stop['stop_points']:
            for key in specific_stop.keys():
                if key in ['code', 'stop_id', 'stop_lat', 'stop_lon', 'stop_name']:
                    stops['specific_stop_' + key].append(specific_stop[key])
            for key in ['stop_id', 'stop_name', 'code', 'distance']:
                stops[key].append('')

    pd.DataFrame(stops).to_csv(filename, index=False)
    

def nameToStopId(name):
    stops = pd.read_csv('all_stops.csv')
    if name in list(stops['stop_name']):
        return stops[stops['stop_name'] == name].iloc[0]['stop_id']
    elif name in list(stops['specific_stop_stop_name']):
        return stops[stops['specific_stop_stop_name'] == name].iloc[0]['specific_stop_stop_id']
    else:
        return None
    

def cumtd_csv_to_sqlite(csv_file, table_name, sqlite_file):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    columns = {'trip_id': 'VARCHAR(60) NOT NULL', 'arrival_time': 'VARCHAR(8) NOT NULL', 'stop_id': 'VARCHAR(17) NOT NULL', 'stop_sequence': 'INTEGER', 'stop_headsign': 'VARCAHAR(36) NOT NULL', 'arrival_id': 'VARCHAR(63) NOT NULL PRIMARY KEY'}
    create_table_str = "CREATE TABLE IF NOT EXISTS {} (".format(table_name)
    for colname, coltype in columns.items():
        create_table_str += colname + " " + coltype + ","
    create_table_str = create_table_str[:-1] + ");"
    c.execute(create_table_str)
    
    csv_df = pd.read_csv(csv_file)
    for row in csv_df.iterrows():
        cmd_str = "INSERT OR IGNORE INTO stop_times(trip_id,arrival_time,stop_id,stop_sequence,stop_headsign,arrival_id) VALUES ("
        trip_id = row[1]['trip_id']
        arrival_time = row[1]['arrival_time']
        stop_id = row[1]['stop_id']
        stop_sequence = row[1]['stop_sequence']
        stop_headsign = row[1]['stop_headsign']
        arrival_id = trip_id + " " + arrival_time # unique arrival identifier
        cmd_str += "'{}', '{}', '{}', {}, '{}', '{}')".format(trip_id, arrival_time, stop_id, stop_sequence, stop_headsign, arrival_id)
        c.execute(cmd_str)
    
    conn.commit()
    conn.close()


def update_db(arrival_date, diff, trip_id, arrival_time, db_file = 'stop_times.db', debug = True):
    db_name = db_file[:-3]
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    new_row = True
    for row in c.execute("PRAGMA table_info('{}')".format(db_name)):
        if row[1] == arrival_date:
            new_row = False
    if new_row:
        c.execute("ALTER TABLE {} ADD '{}' INTEGER(4) DEFAULT -1".format(db_name, arrival_date))

    exec_str = "UPDATE {} SET '{}' = {} WHERE arrival_id = '{}';".format(db_name, arrival_date, diff, trip_id + " " + arrival_time)
    c.execute(exec_str)

    conn.commit()
    conn.close()


def parse_store_cumtd_data(result, debug = True):
    if 'departures' not in result:
        if debug: print("{}: error getting departures: {}".format(datetime.now(), result['status']['msg']))
    else:
        for departure in result['departures']:
            if (departure['is_scheduled']):
                trip_id = departure['trip']['trip_id']
                scheduled_time = datetime.fromisoformat(departure['scheduled'])
                diff = (datetime.fromisoformat(departure['expected']) - scheduled_time).seconds
                arrival_date, arrival_time = str(scheduled_time).split(' ')
                if scheduled_time.hour <= 6:
                    arrival_date = str(scheduled_time - timedelta(1,0))[:10]
                    arrival_time = str(int(arrival_time[:2]) + 24) + arrival_time[2:-6]
                else:
                    arrival_time = arrival_time[:-6]
                update_db(arrival_date, diff, trip_id, arrival_time, debug = True)
            else:
                print("{}: unscheduled ride: {}".format(datetime.now(), result))
        if debug: print("{}: finished analyzing {}: {} departures logged".format(datetime.now(), result['rqst']['params']['stop_id'].upper(), len(result['departures'])))


def has_stops(stop_id, minutes, db_file = 'stop_times.db', debug = True):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    for stop in c.execute("SELECT arrival_time FROM {0} WHERE stop_id LIKE '{1}:%' OR stop_id LIKE '{1}' ORDER BY arrival_time".format(db_file[:-3], stop_id)):
        other_time = [int(x) for x in stop[0].split(":")]
        if other_time[0] > 23: other_time[0] -= 24
        now_time = datetime.now().time()
        if timedelta(minutes=0) < timedelta(hours=other_time[0], minutes=other_time[1], seconds=other_time[2]) \
            - timedelta(hours=now_time.hour, minutes=now_time.minute, seconds=now_time.second) < timedelta(minutes=minutes):
            conn.close()
            if debug: print("{}: {} has a stop within next {} minutes".format(datetime.now(), stop_id, minutes))
            return True
    if debug: print("{}: {} does not have a stop within next {} minutes".format(datetime.now(), stop_id, minutes))
    conn.close()
    return False


def analyze_all_stops(stops, minutes_between, debug):
    start = datetime.now()
    stops_analyzed = 0
    for stop_id in stops:
        if has_stops(stop_id, minutes_between, 'stop_times.db', debug):
            r = requests.get(cumtdRequestUrl("getdeparturesbystop", {'stop_id': stop_id, 'pt': minutes_between}))
            parse_store_cumtd_data(r.json(), debug)
            stops_analyzed += 1
        time.sleep(3)
    print("{}: finished analyzing {} stops in {}".format(datetime.now(), stops_analyzed, datetime.now() - start))



def setup():
	# initial creation of database 
	cumtd_csv_to_sqlite('google_transit/stop_times.txt', 'stop_times', 'stop_times.db')

	# run once per folder
	generateAllStopsCsv('all_stops.csv')


def main():
	debug = True
	minutes_between = 60

	stop_times_all = pd.read_csv('google_transit/stop_times.txt')

	all_stops = stop_times_all.loc[:]['stop_id']
	stops = set([x[:-2] if re.match(".+:\w{1}", x) else x for x in all_stops])
	stops = sorted(stops)


	while True:
	    analyze_all_stops(stops, minutes_between, debug)

	    while datetime.now().time().minute != 0:
	        time.sleep(60)
	    print("{}: starting next round".format(datetime.now()))

if __name__ == "__main__":
	# setup()
	main()

