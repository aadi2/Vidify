from flask import Flask, jsonify
import os

app = Flask(__name__)


@app.route("/", methods=["POST"])
def home():
    result = {"message": "Request Received."}

    return jsonify(result), 200


if __name__ == "__main__":
    if not os.path.exists("temp"):
        os.makedirs("temp")
    app.run(debug=True, host="0.0.0.0", port=8000)
