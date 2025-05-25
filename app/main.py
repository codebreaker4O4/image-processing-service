from flask import Flask, app
from app.routes import auth, image

app = Flask(__name__)
app.secret_key = "" # Set a secret key for session management

# Register routes
app.register_blueprint(auth.bp)
app.register_blueprint(image.bp)

if __name__ == "__main__":
    app.run(debug=True)  # Run the app in debug mode