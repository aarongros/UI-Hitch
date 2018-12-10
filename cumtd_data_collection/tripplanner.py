# use gettripsbylatlon to find trips

from cumtd_data_collection import cumtd_request_url
import requests

class TripPlanner:
    def __init__(self, orig_lat, orig_lon, dest_lat, dest_lon, max_walk, max_wait):
        # to make call:
        # requests.get(cumtd_request_url(methodname, {'extra_params': param}))
        self._orig = [orig_lat, orig_lon]
        self._dest = [dest_lat, dest_lon]
        self._max_walk = max_walk
        self._max_wait = max_wait

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
            {"stop_id", stop_id}))
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
    trip_planner.get_directions()
