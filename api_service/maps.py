import os
import json
import requests

class Maps:
    
    def __init__(self):
        with open(os.getenv("GOOGLE_MAPS_API_KEY")) as f:
            self.MAPS_API_KEY = json.load(f)["api_key"]

    #TODO: we need a custom function get_nearby_interests to pass in the interest from users dynamically 
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