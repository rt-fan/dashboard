from flask import Flask, render_template
import ast
import logging
import json

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/')
def index():
    with open("time.txt") as file:
        time_now = file.read()

    with open("areas.txt") as file:
        a = file.read()
        areas = ast.literal_eval(a)

    with open("employees.txt") as file:
        b = file.read()
        employees = ast.literal_eval(b)

    names = sorted(employees)
    return render_template('index.html', names=names, areas=areas, employees=employees, time=time_now)


@app.route('/new')
def index2():
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        employees = data['employees']
        datetime_request = data['datetime']
        return render_template('index2.html', employees=employees, datetime_request=datetime_request)


@app.route('/3')
def index3():
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        employees = data['employees']
        datetime_request = data['datetime']
        return render_template('index3.html', employees=employees, datetime_request=datetime_request)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
