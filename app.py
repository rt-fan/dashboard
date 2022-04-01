from flask import Flask, render_template
import ast

app = Flask(__name__)


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



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
