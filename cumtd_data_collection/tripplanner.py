# use gettripsbylatlon to find trips

from cumtd_data_collection import cumtd_request_url
import requests

class TripPlanner:
    def __init__(self):
        # to make call:
        # requests.get(cumtd_request_url(methodname, {'extra_params': param}))
