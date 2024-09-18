from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
import os, time, threading, requests
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Check if all necessary environment variables are present
postgres_host = os.getenv('POSTGRES_HOST')
postgres_port = os.getenv('POSTGRES_PORT')
postgres_user = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')
postgres_db = os.getenv('POSTGRES_DB')
schema_name = os.getenv('CHAIN')

# Ensure all values are set
if not postgres_host or not postgres_port or not postgres_user or not postgres_password or not postgres_db or not schema_name:
    raise ValueError("One or more required PostgreSQL environment variables are missing.")

# Configure PostgreSQL database using environment variables
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{int(postgres_port)}/{postgres_db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Create the table within the specified schema if it doesn't exist
with app.app_context():
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {schema_name}.traffic_data (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
        location VARCHAR(80),
        speed FLOAT,
        jam_factor FLOAT,
        bbox VARCHAR(120),
        filter_value VARCHAR(80)
    );
    """
    db.session.execute(text(create_table_sql))
    db.session.commit()

# Database model for traffic data
class TrafficData(db.Model):
    __tablename__ = 'traffic_data'
    __table_args__ = {'schema': schema_name}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Timezone-aware
    location = db.Column(db.String(80))
    speed = db.Column(db.Float)
    jam_factor = db.Column(db.Float)
    bbox = db.Column(db.String(120))
    filter_value = db.Column(db.String(80))

# Class for handling API requests
class TrafficAPIClient:
    BASE_URL = "https://data.traffic.hereapi.com/v7/flow"
    
    def __init__(self, bbox=None, filter_desc=None):
        self.api_key = os.getenv("API_KEY")
        self.bbox = bbox or tuple(map(float, os.getenv("BBOX").split(',')))
        self.filter = filter_desc or os.getenv("FILTER")
        
    def get_traffic_flow(self):
        params = {
            "locationReferencing": "shape",
            "in": f"bbox:{self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]}",
            "apiKey": self.api_key
        }
        response = requests.get(self.BASE_URL, params=params)
        return response.json() if response.status_code == 200 else {}

    def filter_results_by_description(self, data):
        filtered_results = [
            result for result in data.get('results', [])
            if self.filter.lower() in result['location']['description'].lower()
        ]
        return filtered_results

# Endpoint to collect traffic data every 5 seconds for an hour and store in the database
@app.route('/traffic-db')
def traffic_db():
    def run_for_hour():
        client = TrafficAPIClient()
        end_time = datetime.now(timezone.utc) + timedelta(hours=1)  # Timezone-aware
        while datetime.now(timezone.utc) < end_time:  # Timezone-aware
            traffic_data = client.get_traffic_flow()
            filtered_traffic_data = client.filter_results_by_description(traffic_data)
            for result in filtered_traffic_data:
                new_entry = TrafficData(
                    location=result['location']['description'],
                    speed=result['currentFlow']['speed'],
                    jam_factor=result['currentFlow']['jamFactor'],
                    bbox=str(client.bbox),
                    filter_value=client.filter
                )
                db.session.add(new_entry)
                db.session.commit()
            time.sleep(5)  # Wait 5 seconds before fetching again

    thread = threading.Thread(target=run_for_hour)
    thread.start()
    
    return jsonify({"message": "Data collection started for 1 hour"}), 200

# Endpoint to display data collected over the last hour
@app.route('/traffic-db-view')
def traffic_db_view():
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)  # Timezone-aware
    traffic_data = TrafficData.query.filter(TrafficData.timestamp >= one_hour_ago).all()

    data = [{"time": td.timestamp, "location": td.location, "speed": td.speed} for td in traffic_data]
    return render_template('db_view.html', data=json.dumps(data))

# Endpoint to allow users to override bbox and filter
@app.route('/traffic-env', methods=['POST'])
def traffic_env():
    bbox = request.json.get('bbox')
    filter_value = request.json.get('filter')

    if bbox:
        os.environ['BBOX'] = ','.join(map(str, bbox))
    if filter_value:
        os.environ['FILTER'] = filter_value

    return jsonify({"message": "Environment variables updated", "bbox": bbox, "filter": filter_value}), 200

if __name__ == "__main__":
    app.run(debug=True)
