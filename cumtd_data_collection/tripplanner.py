# use gettripsbylatlon to find trips

from cumtd_data_collection import cumtd_request_url
import requests, sys, copy, json
from pprint import pprint
from datetime import datetime, timedelta


class TripPlanner:
    def __init__(self, orig_lat, orig_lon, dest_lat, dest_lon, max_walk, max_wait):
        # to make call:
        # requests.get(cumtd_request_url(methodname, {'extra_params': param}))
        self._orig = [orig_lat, orig_lon]
        self._dest = [dest_lat, dest_lon]
        self._max_walk = max_walk
        self._max_wait = max_wait
        
    def get_directions(self):
        return self._sorted_trips
    
    def get_old_directions(self):
        return self._old_trips['itineraries']
    
    def search(self):
        # overview:
        # 1) get trip
        # 2) edit all services to have accurate times
        # 3) look for any inconsistencies + negative times
        # 4) sort by total travel time

        trips = self._get_trip()
        self._old_trips = copy.deepcopy(trips)
        if 'itineraries' not in trips:
            raise Exception('no trips available')
        
        for trip in trips['itineraries']:
            self._edit_trip(trip)

        self._trips = filter(self._find_inconsistencies, trips['itineraries'])

        for trip in trips['itineraries']:
            self._find_travel_time(trip)

        self._sort_trips_by_time()
    
    def _edit_trip(self, trip):
        # edit all services to have accurate time (don't edit walk)
        for leg in trip['legs']:
            if leg['type'] == 'Service':
                for service in leg['services']:
                    trip_id = service['trip']['trip_id']
                    # begin service leg
                    begin_stop_id = service['begin']['stop_id']
                    departures = self._get_departures_by_stop(begin_stop_id)['departures']
                    for departure in departures:
                        if departure['trip']['trip_id'] == trip_id:
                            service['begin']['time'] = departure['scheduled']
                            break
                    
                    # repeat same thing for end service leg
                    end_stop_id = service['end']['stop_id']
                    departures = self._get_departures_by_stop(end_stop_id)
                    for departure in departures['departures']:
                        if departure['trip']['trip_id'] == trip_id:
                            service['end']['time'] = departure['scheduled']
                            break

    def _find_inconsistencies(self, trip):
        # find any inconsistent trips, used in filter
        # look for trips that have start and end times that don't work
        all_legs = []
        for leg in trip['legs']:
            if leg['type'] == 'Walk':
                all_legs.append(leg['walk'])
            else:
                for _leg in leg['services']: all_legs.append(_leg)
        
        for i in range(1, len(all_legs)):
            start_next_leg = self._strptime(all_legs[i]['begin']['time'])
            end_last_leg = self._strptime(all_legs[i-1]['end']['time'])
            if (start_next_leg - end_last_leg).total_seconds() < 0:
                return False
        return True
        

    def _find_travel_time(self, trip):
        # find total travel time for trip
        if trip['legs'][-1]['type'] == 'Walk':
            trip['end_time'] = trip['legs'][-1]['walk']['end']['time']
        else:
            trip['end_time'] = trip['legs'][-1]['services'][-1]['end']['time']
        
        # time traveling vs time waiting is probably different
        total_travel_time = 0
        for leg in trip['legs']:
            if leg['type'] == 'Walk':
                start_time = self._strptime(leg['walk']['begin']['time'])
                end_time = self._strptime(leg['walk']['end']['time'])
                total_travel_time += (end_time - start_time).total_seconds()
            elif leg['type'] == 'Service':
                for service in leg['services']:
                    start_time = self._strptime(service['begin']['time'])
                    end_time = self._strptime(service['end']['time'])
                    total_travel_time += (end_time - start_time).total_seconds()
        
        start_time = self._strptime(trip['start_time'])
        end_time = self._strptime(trip['end_time'])
        clock_time = (end_time - start_time).total_seconds()
    
        # update time in dict as minutes 
        trip['travel_time'] = clock_time / 60
        trip['total_wait'] = (clock_time - total_travel_time) / 60

    def _sort_trips_by_time(self):
        sorted_by_wait = sorted(self._trips, key=lambda x: x['total_wait'])
        self._sorted_trips = sorted(sorted_by_wait, key=lambda x: x['travel_time'])


    def _strptime(self, time):
        # parse times, should all be in same format
        if time[-3:-2] == ':':
            time = time[:-3] + time[-2:]
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")

    def _get_trip(self):
        # see https://developer.cumtd.com/documentation/v2.2/method/getplannedtripsbylatlon/
        r = requests.get(cumtd_request_url("getplannedtripsbylatlon",
            {"origin_lat": self._orig[0], "origin_lon": self._orig[1],
            "destination_lat": self._dest[0], "destination_lon": self._dest[1],
            "max_walk": self._max_walk}))
        return r.json()
    
    def _get_departures_by_stop(self, stop_id):
        # see https://developer.cumtd.com/documentation/v2.2/method/getplannedtripsbylatlon/
        r = requests.get(cumtd_request_url("getdeparturesbystop",
            {"stop_id": stop_id}))
        return r.json()

def main():
    # allen hall
    origin_lat = 40.1041069
    origin_lon = -88.220894
    # siebel
    dest_lat = 40.1138028
    dest_lon = -88.2249052
    
    max_walk = 1
    max_wait = 20
    
    trip_planner = TripPlanner(origin_lat, origin_lon, dest_lat, dest_lon, max_walk, max_wait)
    trip_planner.search()
    # trip_planner.get_old_directions()
    pprint(trip_planner.get_directions())


if __name__ == "__main__":
    sys.exit(main())
