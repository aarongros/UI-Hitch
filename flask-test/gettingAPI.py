
#Just a test file


import requests
import json
import keys

# parameters = {'q': 'eceb, illinois', 'locale': 'en', 'debug': 'true', 'limit': '15', 'key': keys.graphhopper_key}
# response = requests.get("https://graphhopper.com/api/1/geocode", params = parameters)
# parameters = {'api_key': keys.openrouteservice_key, 'text': 'Namibian Brewery'}
# response = requests.get("https://api.openrouteservice.org/geocode/search", params = parameters)
# parameters = {'access_key': keys.ipstack_key}
# response = requests.get("http://api.ipstack.com/check", params = parameters)
# data = response.json()

parameters = {'access_key': keys.ipstack_key}
response = requests.get("http://api.ipstack.com/check", params = parameters)
currentLocation = response.json()
currentLongitude = currentLocation['longitude']
currentLatitude = currentLocation['latitude']
parameters = {'api_key': keys.openrouteservice_key, 'text': 'thomas siebel', 'focus.point.lat': currentLatitude, 'focus.point.lon': currentLongitude, 'boundary.country': 'US'}
response = requests.get("https://api.openrouteservice.org/geocode/search", params = parameters)
json_obj = response.json()
coordinates = []
results = []
counter = 0
for elem in json_obj['features']:
	results.append({})
	results[counter]['label'] = elem['properties']['label']
	coordinates.append(elem['geometry']['coordinates'])
	results[counter]['longitude'] = coordinates[len(coordinates)-1][0]
	results[counter]['latitude'] = coordinates[len(coordinates)-1][1]
	counter += 1


parameters = {'key': keys.cumtd_key, 'origin_lat': currentLatitude, 'origin_lon': currentLongitude, 'destination_lat': results[0]['latitude'], 'destination_lon': results[0]['longitude']}
response = requests.get("https://developer.cumtd.com/api/v2.2/json/getplannedtripsbylatlon", params = parameters)
data = response.json()
print(str(data))
routes = []
for itinerarie in data['itineraries']:

    for elem in itinerarie["legs"]:
        if elem['type'] == "Service":
            shapeid = []
            beginstopid = []
            endstopid = []
            for service in elem['services']:
                shapeid.append(service['trip']['shape_id'])
                beginstopid.append(service['begin']['stop_id'])
                endstopid.append(service['end']['stop_id'])

    routes.append()
# parameters = {'key': keys.cumtd_key, 'begin_stop_id' : '', 'end_stop_id': '', 'shape_id': ''}
# response = requests.get("https://developer.cumtd.com/api/v2.2/json/getshapebetweenstops", params = parameters)
# data = response.json()
