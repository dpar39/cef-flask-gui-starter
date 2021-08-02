from flask import Flask
import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_url_path="", static_folder='gui/dist/gui')


@app.route('/', methods=['GET'])
def index():
    return app.send_static_file("index.html")
