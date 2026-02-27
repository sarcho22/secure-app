from flask import Flask
import config

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

@app.route('/')
def index():
    return 'Hello, Flask!'

if __name__ == '__main__':
    app.run(debug=True)