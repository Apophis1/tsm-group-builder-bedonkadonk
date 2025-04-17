from flask import Flask
from flask_cors import CORS
from scraper.scraper import scraper_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(scraper_bp)

@app.route("/ping", methods=["GET"])
def ping():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(debug=True)
