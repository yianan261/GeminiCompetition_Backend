import os
import google.generativeai as genai

class LLMTools:

    MODEL_ID = "gemini-1.5-pro-001"
    POSSIBLE_PLACE_TYPES = [
        "amusement_park", "aquarium", "art_gallery", "bakery", "bar", "beauty_salon", "book_store", "bowling_alley",
        "cafe", "campground", "casino", "cemetery", "church", "city_hall", "clothing_store", "convenience_store",
        "department_store", "drugstore", "electronics_store", "florist", "gym", "hair_care", "hardware_store",
        "hindu_temple", "jewelry_store", "library", "liquor_store", "lodging", "meal_takeaway", "mosque",
        "movie_theater", "museum", "night_club", "painter", "park", "restaurant", "shoe_store", "shopping_mall",
        "spa", "stadium", "store", "supermarket", "tourist_attraction", "university", "veterinary_care", "zoo"
    ]

    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel(self.MODEL_ID)
    
    def test_api(self):
        response = self.model.generate_content("Write a story about an AI")
        return response.text


