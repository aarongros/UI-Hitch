from flask import Flask, render_template, request, flash
import requests, json, keys
from tripplanner import TripPlanner
from thinned_directions import get_thinned_directions

result = []

app = Flask(__name__)

stations = [
	{
		'name': 'Ike',
		'time': '2'
	},
	{
		'name': 'Transit',
		'time': '5'
	},
	{
		'name': 'Union',
		'time': '1'
	}
]

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/schedule', methods=['POST'])
def schedule():
	try:
		destination = request.form['destination']
	except:
		print("DESTINATION FAILED!!!!")

	parameters = {'access_key': keys.ipstack_key}
	response = requests.get("http://api.ipstack.com/check", params = parameters)
	currentLocation = response.json()
	currentLongitude = currentLocation['longitude']
	currentLatitude = currentLocation['latitude']
	origin_value = str(currentLatitude) + "," + str(currentLongitude)
	
	tripPlanner = TripPlanner(origin_value, destination)
	tripPlanner.search()
	
	data = tripPlanner.get_directions()
	arrival_times = []
	for itinerary in data:
		try:
			arrival_times.append(itinerary['legs'][0]['arrival_time']['text'])
		except:
			continue
	return render_template('schedule.html', arrival_times=arrival_times, data=data)

@app.route('/signup')
def signup():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/map', methods=['POST'])
def map():
	selection = request.form['selection']
	return render_template('map.html', itineraries = get_thinned_directions(selection))

@app.route('/search')
def search():
	return render_template('search.html')

@app.route('/results', methods=['POST'])
def results():
	destination = request.form['destination']
	
	parameters = {'access_key': keys.ipstack_key}
	response = requests.get("http://api.ipstack.com/check", params = parameters)
	currentLocation = response.json()
	currentLongitude = currentLocation['longitude']
	currentLatitude = currentLocation['latitude']
	parameters = {'api_key': keys.openrouteservice_key, 'text': destination, 'focus.point.lat': currentLatitude, 'focus.point.lon': currentLongitude, 'boundary.country': 'US'}
	response = requests.get("https://api.openrouteservice.org/geocode/search", params = parameters)
	json_obj = response.json()
	coordinates = []
	counter = 0
	for elem in json_obj['features']:
		result.append({})
		result[counter]['label'] = elem['properties']['label']
		coordinates.append(elem['geometry']['coordinates'])
		result[counter]['longitude'] = coordinates[len(coordinates)-1][0]
		result[counter]['latitude'] = coordinates[len(coordinates)-1][1]
		counter += 1
	return render_template('results.html', results = result)

if __name__ == '__main__':
	app.run(debug=True)
