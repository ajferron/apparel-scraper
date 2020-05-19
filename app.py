from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/auth')
def auth():
    return render_template('auth.html')


@app.route('/submit', methods=['POST'])
def submit():
    return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
