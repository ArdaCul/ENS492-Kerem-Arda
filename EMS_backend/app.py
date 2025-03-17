from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='../frontend')

@app.route("/")
def home():
    return send_from_directory(app.static_folder, 'homepage.tsx')

if __name__ == "__main__":
    app.run(debug=True)
