from flask import Flask, app
from app.routes import auth, image
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Register routes
app.register_blueprint(auth.bp)
app.register_blueprint(image.bp)
print("Running main.py from:", __name__)
@app.route("/")
def home():
    return "Flask server is running ✅"

if __name__ == "__main__":
    app.run(debug=True)  # Run the app in debug mode