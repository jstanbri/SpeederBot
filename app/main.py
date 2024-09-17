import os
import requests
from dotenv import load_dotenv
import json

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
            return response.json()  # Parsed JSON object (Python dictionary)
        else:
            return {"error": response.status_code, "message": response.text}

    def filter_results_by_description(self, data, description):
        """
        Filter the traffic data results by location description.

        :param data: Traffic data JSON
        :param description: The description to filter by (e.g., "Tangmere")
        :return: Filtered traffic data
        """
        filtered_results = [result for result in data.get('results', []) if result['location']['description'] == description]
        return filtered_results

    def traffic_data_to_geojson(self, data):
        """
        Convert traffic data to GeoJSON format for map visualization.
        """
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for result in data:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [point["lng"], point["lat"]] for point in result["location"]["shape"]["links"][0]["points"]
                    ]
                },
                "properties": {
                    "description": result["location"]["description"],
                    "speed": result["currentFlow"]["speed"],
                    "jamFactor": result["currentFlow"]["jamFactor"]
                }
            }
            geojson["features"].append(feature)

        return geojson
    def get_schema(self, data, depth=1, max_samples=1):
        """
        Recursively extract the schema from the JSON data.
        """
        if depth > 13:  # Increase the depth limit
            return 'Too deep'
        
        if isinstance(data, dict):
            schema = {}
            for key, value in data.items():
                schema[key] = self.get_schema(value, depth + 1, max_samples)
            return schema
        
        elif isinstance(data, list):
            if len(data) > 0:
                return [self.get_schema(data[0], depth + 1, max_samples)]  # Only look at the first element
            else:
                return 'Empty list'
        
        else:
            return type(data).__name__  # Return the type for base values (e.g., str, int, etc.)


    def save_geojson(self, geojson_data, filename="traffic_data.geojson"):
        """
        Save the GeoJSON data to a file.
        
        :param geojson_data: The GeoJSON data object
        :param filename: The filename for the saved GeoJSON file
        """
        with open(filename, "w") as geojson_file:
            json.dump(geojson_data, geojson_file, indent=4)


if __name__ == "__main__":
    # Example bounding box coordinates
    # Use http://bboxfinder.com/
    bbox = (-0.722437,50.846435,-0.712888,50.855701)
    """ bbox = (-0.787759,50.846435,-0.715806,50.854346) """
    
    client = TrafficAPIClient()
    traffic_data = client.get_traffic_flow(bbox)
    
    # Filter traffic data by description for "Tangmere"
    tangmere_traffic_data = client.filter_results_by_description(traffic_data, description="Tangmere")
   
    
    # Get the schema
    schema = client.get_schema(traffic_data)
    
    if tangmere_traffic_data:
        # Convert filtered traffic data to GeoJSON and save it
        geojson_data = client.traffic_data_to_geojson(tangmere_traffic_data)
        client.save_geojson(geojson_data, filename="tangmere_traffic_data.geojson")

        print("Traffic data saved as traffic_data.json")  # For logging, replace with logging module if needed
        print(json.dumps(schema, indent=4))
    else:
        print("No traffic data found for Tangmere")