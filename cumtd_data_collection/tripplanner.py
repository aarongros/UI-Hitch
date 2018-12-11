# use gettripsbylatlon to find trips

import googlemaps
from apikey import keys
from cumtd_data_collection import cumtd_request_url
import requests, sys, copy, json, csv, pprint
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
        if len(trips) == 0:
            raise Exception("no trips available")
        self._old_trips = copy.deepcopy(trips)
        
        for trip in trips:
            self._edit_trip(trip)

        self._trips = list(filter(self._find_inconsistencies, trips))
        if len(self._trips) == 0 and len(self._old_trips) != 0:
            pprint.pprint(self._old_trips)
            raise Exception("no filtered trips available, returned old")

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
                stop_loc = transit['departure_stop']['location']
                begin_stop_id = self._to_stop_id(stop_name, stop_loc['lat'], stop_loc['lng'])
                departures = self._get_departures_by_stop(begin_stop_id)
                for departure in departures['departures']:
                    if departure['route']['route_id'].lower() == transit['line']['name'].lower():
                        real_time = departure['expected']
                        real_time_full = self._strptime(real_time)
                        real_time_12hr = datetime.strftime(real_time_full, "%I:%M:%S%p")
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
                stop_loc = transit['arrival_stop']['location']
                end_stop_id = self._to_stop_id(stop_name, stop_loc['lat'], stop_loc['lng'])
                departures = self._get_departures_by_stop(end_stop_id)['departures']
                for departure in departures:
                    if departure['route']['route_id'].lower() == transit['line']['name'].lower():
                        real_time = departure['expected']
                        real_time_full = self._strptime(real_time)
                        real_time_12hr = datetime.strftime(real_time_full, "%I:%M%p")
                        real_time_int = int(real_time_full.timestamp())
                        # put them back into the schedule
                        transit['arrival_time'] = {
                            'text': real_time_12hr,
                            'time_zone': 'America/Chicago',
                            'value': real_time_int
                        }
                        break
                duration = transit['arrival_time']['value'] - transit['departure_time']['value']
                if duration < 0:
                    # TODO: do something?
                    pass
                leg['duration']['value'] = duration
                leg['duration']['text'] = "{0:.2f} mins".format(duration / 60)
        # end time doesn't change UNLESS last leg is bus
        # maybe do another call to API to figure out whether person can walk from bus endpoint
        # to destination?


    def _to_stop_id(self, stop_name, lat, lon):
        stop_name = stop_name.replace(" and ", " & ")
        with open('google_transit/stops.txt', 'rt') as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None) # skip header line
            for row in csv_reader:
                row_lat = float(row[4])
                row_lon = float(row[5])
                if row[2] == stop_name:
                    # column stop_name
                    return row[0]
                elif abs(row_lat - lat) < 1e-4 and abs(row_lon - lon) < 1e-4:
                    # colum stop_lon
                    return row[0]
        raise Exception("stop {} not found!".format(stop_name))

    def _find_inconsistencies(self, trip):
        times = [trip['legs'][0]['departure_time']['value']]
        for leg in trip['legs'][0]['steps']: # is this okay?
            if leg['travel_mode'] == 'WALKING':
                times.append(times[-1] + leg['duration']['value'])
            elif leg['travel_mode'] == 'TRANSIT':
                transit = leg['transit_details']
                if transit['departure_time']['value'] < times[-1]:
                    print("bus came early and ruined trip. finding new trip to here")
                    return False
                else:
                    times.append(transit['arrival_time']['value'])
        return True


    def _find_travel_time(self, trip):
        total_travel_time = 0
        for leg in trip['legs'][0]['steps']:
            total_travel_time += leg['duration']['value']
        trip['travel_time'] = {'value': total_travel_time,
                               'text': "{0:.2f} mins".format(total_travel_time / 60)}
        total_time = trip['legs'][0]['arrival_time']['value'] - trip['legs'][0]['departure_time']['value']
        wait_time = total_time - total_travel_time
        trip['wait_time'] = {'value': wait_time,
                               'text': "{0:.2f} mins".format(wait_time / 60)}

    def _sort_trips_by_time(self):
        self._sorted_trips = sorted(self._trips, key=lambda x: self._calculate_weighted_score(x))
       
    def _calculate_weighted_score(self, trip):
        return 0.8 * trip['travel_time']['value'] + 0.2 * trip['wait_time']['value'] 

    def _strptime(self, time):
        # parse times, should all be in same format
        if time[-3:-2] == ':':
            time = time[:-3] + time[-2:]
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")

    def _get_trip(self):
        gmaps = googlemaps.Client(key=keys['google'])
        directions_result = gmaps.directions(self._orig, self._dest, mode="transit", departure_time=datetime.now(), alternatives=True)
        return directions_result
    
    def _get_departures_by_stop(self, stop_id):
        # see https://developer.cumtd.com/documentation/v2.2/method/getplannedtripsbylatlon/
        r = requests.get(cumtd_request_url("getdeparturesbystop",
            {"stop_id": stop_id}))
        result_json = r.json()
        if result_json['status']['code'] != 200:
            raise Exception("error calling CUMTD API: {}".format(result_json['status']['msg']))
        return r.json()

    def pprint_to_file(self, obj, fout):
        pp = pprint.PrettyPrinter(stream=open(fout,'w'))
        pp.pprint(obj)

def main():
    start = "Siebel Center for Computer Science"
    end = "The University of Illinois - Memorial Stadium"
    trip_planner = TripPlanner(start, end)
    trip_planner.search()
    trip_planner.pprint_to_file(trip_planner.get_old_directions(), "old_directions.txt")
    pprint.pprint(trip_planner.get_directions())

if __name__ == "__main__":
    sys.exit(main())
