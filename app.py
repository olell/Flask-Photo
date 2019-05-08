from flask import Flask
from flask_photo import view

app = Flask(__name__)
app.secret_key = "important, use something secret here!"

app.register_blueprint(view, url_prefix="/gallery")

@app.route("/")
def index():
    return "<html><head><title>Flask Photo Example</title></head><body><h1>This is an example for Flask Photo.</h1></body></html>"