import os
import json
import requests
from bs4 import BeautifulSoup


class Maps:
    
    def __init__(self):
        with open(os.getenv("GOOGLE_MAPS_API_KEY")) as f:
            self.MAPS_API_KEY = json.load(f)["api_key"]

    #TODO: we need a custom function get_nearby_interests to pass in the interestfrom users dynamically 
    def get_nearby_attractions(self, location, radius=None):
        if not radius:
            radius = 5000
        types = "tourist_attraction|museum|park" #this is hardcoded, need to change
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={types}&key={self.MAPS_API_KEY}"

        response = requests.get(url)
        return response

    def get_nearby_restaurants(self, location, radius=None):
        if not radius:
            radius = 5000
        types = "restaurant|cafe|bar|dessert"
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={types}&key={self.MAPS_API_KEY}"

        response = requests.get(url)
        return response

    def get_place_details(self, place_id):
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={self.MAPS_API_KEY}"

        response = requests.get(url)
        return response

    def get_place_id(self, url):
        # Send a GET request to the URL
        response = requests.get(url)

        # Parse the HTML content using Beautiful Soup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the meta tag with itemprop="name"
        meta_tag = soup.find("meta", itemprop="name")

        if meta_tag:
            # Get the content attribute of the meta tag
            place_name = meta_tag.get("content")
        else:
            return None

        query_url = "https://maps.googleapis.com/maps/api/place/queryautocomplete/json"

        # Query parameters
        params = {"input": place_name, "types": "geocode", "key": {self.MAPS_API_KEY}}
        # Send a GET request
        response = requests.get(query_url, params=params)
        predictions = response.json()["predictions"]
        if predictions:
            place_id = predictions[0]["place_id"]
            return place_id
        else:
            return None
