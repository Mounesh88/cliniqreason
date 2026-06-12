from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/")
def home():
    return "CliniqReason is running! ✅"

if __name__ == "__main__":
    app.run(debug=True)