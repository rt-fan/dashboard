from flask import Flask, render_template
import ast
import logging
import json

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/')
def index():
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        employees = data['employees']
        datetime_request = data['datetime']
        return render_template('index.html', employees=employees, datetime_request=datetime_request)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
