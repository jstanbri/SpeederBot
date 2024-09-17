from flask import Flask, jsonify, render_template
import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

class TrafficAPIClient:
    BASE_URL = "https://data.traffic.hereapi.com/v7/flow"
    
    def __init__(self):
        # Get API key, bounding box, and filter from environment variables
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API Key not found in environment variables")

        # Get bounding box from environment and split it into coordinates
        bbox_str = os.getenv("BBOX")
        self.bbox = tuple(map(float, bbox_str.split(','))) if bbox_str else None

        # Get the filter from environment variables
        self.filter = os.getenv("FILTER")
        
        if not self.bbox:
            raise ValueError("Bounding Box not found in environment variables")
        
        if not self.filter:
            raise ValueError("Filter not found in environment variables")
        
    def get_traffic_flow(self):
        """
        Make a GET request to retrieve traffic flow data using the bounding box from .env.
        """
        params = {
            "locationReferencing": "shape",
            "in": f"bbox:{self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]}",
            "apiKey": self.api_key
        }
        
        response = requests.get(self.BASE_URL, params=params)
        
        if response.status_code == 200:
            return response.json()  # Parsed JSON object (Python dictionary)
        else:
            return {"error": response.status_code, "message": response.text}

    def filter_results_by_description(self, data):
        """
        Filter the traffic data results by location description from .env.
        """
        filtered_results = [
            result for result in data.get('results', [])
            if self.filter.lower() in result['location']['description'].lower()
        ]
        return filtered_results


@app.route('/', methods=['GET'])
def home():
    # Initialize the client and fetch traffic data using bbox and filter from .env
    client = TrafficAPIClient()
    traffic_data = client.get_traffic_flow()
    
    # Filter traffic data by description for the filter specified in .env
    filtered_traffic_data = client.filter_results_by_description(traffic_data)
    
    # Prepare the data for the web page
    chart_data = {
        "locations": [result['location']['description'] for result in filtered_traffic_data],
        "speeds": [result['currentFlow']['speed'] for result in filtered_traffic_data],
        "jamFactors": [result['currentFlow']['jamFactor'] for result in filtered_traffic_data]
    }
    
    # Render the HTML page and pass the data
    return render_template('index.html', chart_data=json.dumps(chart_data))


@app.route('/traffic_data')
def traffic_data():
    # Endpoint to return the traffic data as JSON
    client = TrafficAPIClient()
    traffic_data = client.get_traffic_flow()
    filtered_traffic_data = client.filter_results_by_description(traffic_data)
    
    return jsonify(filtered_traffic_data)

if __name__ == "__main__":
    app.run(debug=True)
