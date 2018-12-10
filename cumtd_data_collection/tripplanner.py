from cumtd_data_collection import cumtd_request_url
import requests, sys, csv, math, time
from datetime import datetime, timedelta
from pprint import pprint # to print json for debug

# API given trip planner
# def tripplanner(origin_lat, origin_lon, dest_lat, dest_lon):
#     origin = [origin_lat, origin_lon]
#     dest = [dest_lat, dest_lon]
#     return requests.get(cumtd_request_url("getplanendtripsbylatlon", 
#         {'origin_lat': origin[0], 'origin_lon': origin[1], 
#          'destination_lat': dest[0], 'destination_lon': dest[1]})
#         ).json()

class TripPlanner:
    
    def __init__(self, orig_lat, orig_lon, dest_lat, dest_lon, max_walking=1609.34, max_waiting=20):
        self._orig = [orig_lat, orig_lon]
        self._dest = [dest_lat, dest_lon]
        self._max_walking = max_walking
        self._max_waiting = max_waiting
        self._google_transit_folder_loc = "google_transit/"
        self._stop_lat_index = 4
        self._stop_lon_index = 5
        self._stop_id_index = 0
        self._time_format = "%Y-%m-%dT%H:%M:%S-06:00"
        self._routes = []
        
        # do all calculations
        print("find_possible_walking_routes")
        start_time = time.time()
        self._find_possible_walking_routes()
        print("time taken: {}".format(time.time() - start_time))
        # pprint(self._routes)
        print("get_accurate_bus_arrivals")

        start_time = time.time()
        self._get_accurate_bus_arrivals()
        print("time taken: {}".format(time.time() - start_time))
        # pprint(self._routes)

        print("find_final_walking_instructions")
        start_time = time.time()
        self._find_final_walking_instructions()
        print("time taken: {}".format(time.time() - start_time))
        # pprint(self._routes)

    def _find_possible_walking_routes(self):
        # use getplannedtripsbylatlon to get walking distance + time from
        # origin lat, lon to nearest bus stations
        # account for whether the origin location is the bus stop itself
        # use max_waiting to find departure within waiting time
        
        close_stops = self._get_close_stops(self._orig, self._google_transit_folder_loc + "stops.txt")
        for stop in close_stops:
            walking_leg = requests.get(
                cumtd_request_url('getplannedtripsbylatlon', 
                    {'origin_lat': self._orig[0],
                    'origin_lon': self._orig[1],
                    'destination_lat': stop[self._stop_lat_index],
                    'destination_lon': stop[self._stop_lon_index]})
                ).json()['itineraries']
            if len(walking_leg) == 0:
                continue
            self._routes.append({'legs': [{'time': walking_leg[0]['travel_time'], 'walk': walking_leg[0]['legs'][0]['walk']}]})

    def _get_close_stops(self, loc, stops_txt_file_loc):
        stops = []
        with open(stops_txt_file_loc, 'r') as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None) # skip header
            for row in csv_reader:
                if self._haversine_distance(row[self._stop_lat_index], row[self._stop_lon_index], loc[0], loc[1]) < self._max_walking:
                    stops.append(row)
        return stops

    def _trip_passes_dest(self, start_stop_id, trip_id):
        close_stops = self._get_close_stops(self._dest, self._google_transit_folder_loc + "stops.txt")
        stop_ids = [stop[self._stop_id_index] for stop in close_stops]
        stops = requests.get(
            cumtd_request_url('getstoptimesbytrip',
                {'trip_id': trip_id})
            ).json()
        stops = stops['stop_times']

        origin_station_index = -1
        for i in range(len(stops)):
            # make sure bus stops at destination AFTER start location
            if 'stop_id' in stops[i] and stops[i]['stop_point']['stop_id'] == start_stop_id:
                origin_station_index = i
            if 'stop_id' in stops[i] and stops[i]['stop_point']['stop_id'] in stop_ids and i != -1:
                destination_departures = requests.get(
                    cumtd_request_url('getdeparturesbystop',
                        {'stop_id': stops[i]['stop_point']['stop_id'],
                        'trip_id': trip_id})
                    ).json()['departures']
                for departure in destination_departures:
                    dest_time = departure['expected']
                    return True, dest_time, departure
        return False, None, None
                
    def _get_accurate_bus_arrivals(self):
        # use either stop_times.db or getdeparturesbystop to get accurate bus
        # arrival times for given station
        for route in self._routes:
            stop_id = route['legs'][0]['walk']['end']['stop_id']
            departures = requests.get(
                cumtd_request_url('getdeparturesbystop',
                    {'stop_id': stop_id,
                    'pt': min(self._max_waiting, 60)})
                ).json()['departures']
            for departure in departures:
                passes, dest_time, stop = self._trip_passes_dest(stop_id, departure['trip']['trip_id'])
                if passes:
                    if 'services' not in route or\
                        (datetime.strptime(dest_time, self._time_format) - datetime.strptime(route['service']['dest_time'], self._time_format)).total_seconds() < 0:
                        start_as_datetime = datetime.strptime(departure['expected'], self._time_format)
                        end_as_datetime = datetime.strptime(dest_time, self._time_format)
                        travel_time = (end_as_datetime - start_as_datetime).total_seconds() / 60
                        route['legs'].append({'time': travel_time, 'service': {'dest_time': dest_time, 'arrival': stop}})

    def _find_final_walking_instructions(self):
        # use getplannedtripsbylatlon to get walking distance + time from
        # each destination bus stop to final destination
        # hopefully getplannedtripsbylatlon will only return walking directions
        # since distance should be minimized by now
        for route in self._routes:
            if len(route['legs']) == 1:
                continue
            location = route['legs'][-1]['service']['arrival']['location']
            lat, lon = location['lat'], location['lon']
            final_walking_route = requests.get(
                cumtd_request_url('getplannedtripsbylatlon',
                    {'origin_lat': lat, 'origin_lon': lon,
                    'destination_lat': self._dest[0], 'destination_lon': self._dest[1]})
                ).json()['itineraries']
            if len(final_walking_route) == 0:
                continue
            if 'services' in final_walking_route[0]['legs'][0].keys():
                route['legs'].append({'time': final_walking_route[0]['travel_time'], 'service': final_walking_route[0]['legs'][0]['services']})
                if len(final_walking_route[0]['legs']) > 1:
                    route['legs'].append({'time': final_walking_route[0]['travel_time'], 'walk': final_walking_route[0]['legs'][1]['walk']})
            route['legs'].append({'time': final_walking_route[0]['travel_time'], 'walk': final_walking_route[0]['legs'][0]['walk']})

    def _haversine_distance(self, orig_lat, orig_lon, dest_lat, dest_lon):
        # formula from https://www.movable-type.co.uk/scripts/latlong.html
        R = 6371e3
        phi1 = math.radians(float(orig_lat))
        phi2 = math.radians(float(dest_lat))
        delta_phi = math.radians(float(dest_lat) - float(orig_lat))
        delta_lambda = math.radians(float(dest_lon) - float(orig_lon))
        a = math.sin(delta_phi / 2) ** 2 +\
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c
        return d  # distance in meters

    def _calculate_times(self):
        for route in self._routes:
            travel_time = 0
            for leg in route['legs']:
                travel_time += leg['time']
            route['travel_time'] = travel_time
            route_start_datetime = datetime.strptime(route['legs'][0]['walk']['begin']['time'], self._time_format)
            route_end_datetime = datetime.strptime(route['legs'][-1]['walk']['end']['time'], self._time_format)
            total_time = route_end_datetime - route_start_datetime
            route['wait_time'] = (total_time - timedelta(minutes=travel_time)).total_seconds() / 60
        
    def get_instructions(self):
        self._calculate_times()
        return sorted(sorted(self._routes, key=lambda x: x['wait_time']), key=lambda x: x['travel_time'])

def main():
    orig_lat = 40.1042238
    orig_lon = -88.2208988
    dest_lat = 40.1138069
    dest_lon = -88.2270939
    max_walking = 400 # in meters
    max_waiting = 10
    trip_planner = TripPlanner(orig_lat, orig_lon, dest_lat, dest_lon, max_walking, max_waiting)
    print("complete!")
    pprint(trip_planner.get_instructions())

if __name__ == "__main__":
    sys.exit(main())
