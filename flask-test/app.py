from flask import Flask, render_template, request
import requests, json, keys

result = []
currentLatitude = 0
currentLongitude = 0

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
	selection = request.form['selection']

	print(selection)
	for elem in result:
		print(elem['label'])
		print(result)
		if elem['label'] == selection:
			parameters = {'key': keys.cumtd_key, 'origin_lat': currentLatitude, 'origin_lon': currentLongitude, 'destination_lat': elem['latitude'], 'destination_lon': elem['longitude']}
			response = requests.get("https://developer.cumtd.com/api/v2.2/json/getplannedtripsbylatlon", params = parameters)
			data = response.json()
			return render_template('schedule.html', stations=str(data))

	return render_template('schedule.html')

@app.route('/signup')
def signup():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/map')
def map():
	return render_template('map.html')

@app.route('/search')
def Search():
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
