import requests
import json
import keys

# parameters = {'q': 'eceb, illinois', 'locale': 'en', 'debug': 'true', 'limit': '15', 'key': keys.graphhopper_key}
# response = requests.get("https://graphhopper.com/api/1/geocode", params = parameters)
parameters = {'api_key': keys.openrouteservice_key, 'text': 'Namibian Brewery'}
response = requests.get("https://api.openrouteservice.org/geocode/search", params = parameters)
data = response.json()
print(response.url)
# print(type(data))
# print('.......................')
# x=data['hits']
# print(x)
# y = x[0]
# print('..............')
# print(y)
# c = y['name']
# print('..............')
# print(c)
# for elem in data["hits"]:
#     d = elem["name"]
#     #a = elem["city"]
#     print(d)
