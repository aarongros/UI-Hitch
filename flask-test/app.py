from flask import Flask, render_template
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

@app.route('/schedule')
def schedule():
	return render_template('schedule.html', stations=stations)

@app.route('/signup')
def signup():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('login.html')


if __name__ == "__main__":
	app.run(debug = True)
