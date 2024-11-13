from flask import Flask, render_template, jsonify
import ast
import logging
import json

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/')
def index():
    with open('data/data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        employees = data['employees']
        datetime_request = data['datetime']
        return render_template('index.html', employees=employees, datetime_request=datetime_request)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """
    Endpoint для проверки состояния приложения.
    """
    return jsonify({'status': 'OK'})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
