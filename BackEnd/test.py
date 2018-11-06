from flask import Flask
app = Flask(__name__)

@app.route('/')
def displayText():
	return 'UIUC Hitch'


if __name__ == "__main__":
	app.run()