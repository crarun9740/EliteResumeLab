from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return 'fuck biet'

@app.route('firstpage', method=["GET"])
def firstpage():
    render_template("")

if __name__ == "__main__":
    app.run(debug=True)