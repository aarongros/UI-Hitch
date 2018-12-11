# use gettripsbylatlon to find trips

import googlemaps
from apikey import keys
from cumtd_data_collection import cumtd_request_url
import requests, sys, copy, json, csv
from pprint import pprint
from datetime import datetime, timedelta


class TripPlanner:
    def __init__(self, start, end):
        self._orig = start
        self._dest = end
        
    def get_directions(self):
        return self._sorted_trips
    
    def get_old_directions(self):
        return self._old_trips
    
    def search(self):
        # overview:
        # 1) get trip
        # 2) edit all services to have accurate times
        # 3) look for any inconsistencies + negative times
        # 4) sort by total travel time
        
        trips = self._get_trip()
        self._old_trips = copy.deepcopy(trips)
        
        for trip in trips:
            self._edit_trip(trip)

        self._trips = filter(self._find_inconsistencies, trips)

        for trip in trips:
            self._find_travel_time(trip)

        self._sort_trips_by_time()

    
    def _edit_trip(self, trip):
        # edit all services to have accurate time(don't edit walk)
        for leg in trip['legs'][0]['steps']: # is this okay?
            if leg['travel_mode'] == 'TRANSIT':
                transit = leg['transit_details']
                
                # begin transit leg
                stop_name = transit['departure_stop']['name']
                begin_stop_id = self._to_stop_id(stop_name)
                departures = self._get_departures_by_stop(begin_stop_id)
                for departure in departures['departures']:
                    if departure['route']['route_id'] == transit['line']['name']:
                        real_time = departure['scheduled']
                        real_time_full = self._strptime(real_time)
                        real_time_24hr = datetime.strftime(real_time_full, "%I:%M%p")
                        real_time_int = int(real_time_full.timestamp())
                        # put them back into the schedule
                        transit['departure_time'] = {
                            'text': real_time_12hr,
                            'time_zone': 'America/Chicago',
                            'value': real_time_int
                        }
                        break

                # end transit leg
                stop_name = transit['arrival_stop']['name']
                end_stop_id = self._to_stop_id(stop_name)
                departures = self._get_departures_by_stop(end_stop_id)['departures']
                for departure in departures:
                    if departure['route']['route_id'] == transit['line']['name']:
                        real_time = departure['scheduled']
                        real_time_full = self._strptime(real_time)
                        real_time_24hr = datetime.strftime(real_time_full, "%I:%M%p")
                        real_time_int = int(real_time_full.timestamp())
                        # put them back into the schedule
                        transit['arrival_time'] = {
                            'text': real_time_12hr,
                            'time_zone': 'America/Chicago',
                            'value': real_time_int
                        }
                        break
        # end time doesn't change UNLESS last leg is bus
        # maybe do another call to API to figure out whether person can walk from bus endpoint
        # to destination?


    def _to_stop_id(self, stop_name):
        print(stop_name)
        with open('google_transit/stops.txt', 'rt') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                if row[2] == stop_name:
                    return row[0]
        return None


    def _text_to_seconds(self, text):
        return int(text.split(" min")[0])


    def _find_inconsistencies(self, trip):
        times = [trip['legs'][0]['departure_time']['value']]
        for leg in trip['legs'][0]['steps']: # is this okay?
            if leg['travel_mode'] == 'WALKING':
                times.append(times[-1] + leg['duration']['value'])
            elif leg['travel_mode'] == 'TRANSIT':
                transit = leg['transit_details']
                if transit['departure_time']['value'] < times[-1]:
                    return False
                else:
                    times.append(transit['arrival_time']['value'])
        return True


    def _find_travel_time(self, trip):
        total_travel_time = 0
        for leg in trip['legs'][0]['steps']:
            # both TRANSIT and WALKING have same 'duration' object
            # leg['duration']['text'] is in format: "12 mins" --> convert to seconds
            total_travel_time += self._text_to_seconds(leg['duration']['text'])
        trip['travel_time'] = {'value': total_travel_time,
                               'text': "{} mins".format(total_travel_time / 60)}
        # trip['legs'][0]['duration'] = trip['legs'][0]['arrival_time']['value'] - trip['legs'][0]['departure_time']['value']

    def _sort_trips_by_time(self):
        sorted_by_wait = sorted(self._trips, key=lambda x: x['travel_time'])
        self._sorted_trips = sorted(sorted_by_wait, key=lambda x: x['legs'][0]['duration']['value'])

    def _strptime(self, time):
        # parse times, should all be in same format
        if time[-3:-2] == ':':
            time = time[:-3] + time[-2:]
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")

    def _get_trip(self):
        gmaps = googlemaps.Client(key=keys['google'])
        directions_result = gmaps.directions(self._orig, self._dest, mode="transit", departure_time=datetime.now())
        return directions_result
    
    def _get_departures_by_stop(self, stop_id):
        # see https://developer.cumtd.com/documentation/v2.2/method/getplannedtripsbylatlon/
        r = requests.get(cumtd_request_url("getdeparturesbystop",
            {"stop_id": stop_id}))
        return r.json()

def main():
    start = "Siebel Center for Computer Science"
    end = "Illini Union"
    trip_planner = TripPlanner(start, end)
    trip_planner.search()
    pprint(trip_planner.get_old_directions())
    pprint(trip_planner.get_directions())

if __name__ == "__main__":
    sys.exit(main())
