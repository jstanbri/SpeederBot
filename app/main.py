import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TrafficAPIClient:
    BASE_URL = "https://data.traffic.hereapi.com/v7/flow"
    
    def __init__(self):
        # Get API key from environment variables
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API Key not found in environment variables")
        
    def get_traffic_flow(self, bbox):
        """
        Make a GET request to retrieve traffic flow data.

        :param bbox: A tuple with the bounding box coordinates (min_lon, min_lat, max_lon, max_lat)
        :return: Response JSON or error message
        """
        params = {
            "locationReferencing": "shape",
            "in": f"bbox:{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "apiKey": self.api_key
        }
        
        response = requests.get(self.BASE_URL, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.status_code, "message": response.text}

if __name__ == "__main__":
    # Example bounding box coordinates
    bbox = (13.400, 52.500, 13.405, 52.505)
    
    client = TrafficAPIClient()
    traffic_data = client.get_traffic_flow(bbox)
    
    print(traffic_data)  # You could replace this with logging if you prefer