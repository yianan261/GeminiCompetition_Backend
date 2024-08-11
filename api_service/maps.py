import os
import json
import math
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Maps:

    def __init__(self):
        with open(os.getenv("GOOGLE_KEY")) as f:
            self.MAPS_API_KEY = json.load(f)["GOOGLE_API_KEY"]

    #TODO: we need a custom function get_nearby_interests to pass in the interest from users dynamically 
    def get_nearby_attractions(self, location, radius=5000):
        types = "park|restaurant|museum|tourist_attraction"  # this is hardcoded, need to change
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={types}&key={self.MAPS_API_KEY}"

        response = requests.get(url)
        return response

    def get_nearby_restaurants(self, location, radius=5000):
        types = "restaurant|cafe|bar|dessert"
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={types}&key={self.MAPS_API_KEY}"

        response = requests.get(url)
        return response

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 3959
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return round(distance, 2)

    def _construct_map_details_headers(self):
        return {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.MAPS_API_KEY,
            'X-Goog-FieldMask': ",".join(
                [
                    'id',
                    'displayName',
                    'location',
                    'currentOpeningHours',
                    'formattedAddress',
                    'photos',
                    'reviews',
                    'userRatingCount',
                    'rating',
                    'editorialSummary',
                    'primaryType',
                    'types',
                    'websiteUri',
                    'addressComponents',
                    'plusCode',
                    'priceLevel',
                    'internationalPhoneNumber',
                    'nationalPhoneNumber',
                    'regularOpeningHours',
                    'websiteUri'
                ]
            )
        }

    def _construct_map_headers(self):
        return {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.MAPS_API_KEY,
            'X-Goog-FieldMask': ",".join(
                [
                    'places.id',
                    'places.displayName',
                    'places.location',
                    'places.currentOpeningHours',
                    'places.formattedAddress',
                    'places.photos',
                    'places.reviews',
                    'places.userRatingCount,',
                    'places.rating',
                    'places.editorialSummary',
                    'places.primaryType',
                    'places.types',
                    'places.websiteUri'
                ]
            )
        }

    def _construct_map_nearby_search_payload(self, types, location, radius):
        return {
            "includedTypes": types,
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": location.split(",")[0].strip(),
                        "longitude": location.split(",")[1].strip()
                    },
                    "radius": radius
                }
            },
            "rankPreference": "POPULARITY"
        }

    def _construct_map_text_search_payload(self, query, location, radius=5000, page_size=20):
        return {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": location.split(",")[0].strip(),
                        "longitude": location.split(",")[1].strip()
                    },
                    "radius": radius
                }
            },
            "pageSize": page_size,
            "openNow": True,
            "rankPreference": "RELEVANCE"
        }

    def _get_photo_url(self, photo_reference, max_width=400, max_height=400):
        if photo_reference:
            return f"https://places.googleapis.com/v1/{photo_reference}/media?key={self.MAPS_API_KEY}&maxWidthPx={max_width}&maxHeightPx={max_height}"
        return None

    def _get_reviews(self, reviews, top_n=3):
        sorted_reviews = sorted(reviews, key=lambda x: x.get('rating', 0), reverse=True)[:top_n]
        
        processed_reviews = []
        for review in sorted_reviews:
            processed_reviews.append({
                "author_name": review.get("authorAttribution", {}).get("displayName"),
                "author_url": review.get("authorAttribution", {}).get("uri"),
                "profile_photo_url": review.get("authorAttribution", {}).get("photoUri"),
                "rating": review.get("rating"),
                "text": review.get("text", {}).get("text"),
                "time": review.get("publishTime"),
                "relative_time_description": review.get("relativePublishTimeDescription")
            })
        return processed_reviews

    def _get_address_component(self, place, component_type):
        for component in place.get("addressComponents", []):
            if component_type in component.get("types", []):
                if component_type == "administrative_area_level_1":
                    return component.get("shortText")
                return component.get("longText")
        return None

    def _construct_places_data(self, places, origin):
        constructed_data = []
        origin_lat, origin_lng = map(float, origin.split(','))

        for place in places:
            photos = place.get("photos", [])
            photo_urls = [self._get_photo_url(photo.get("name")) for photo in photos]
            place_info = {
                "place_id": place.get("id"),
                "title": place.get("displayName", {}).get("text"),
                "location": {
                    "latitude": place.get("location", {}).get("latitude"),
                    "longitude": place.get("location", {}).get("longitude")
                },
                "distance": self._calculate_distance(
                    origin_lat, origin_lng,
                    place.get("location", {}).get("latitude"),
                    place.get("location", {}).get("longitude")
                ),
                "address": place.get("formattedAddress", ""),
                "photo_url": photo_urls,
                "reviews": self._get_reviews(place.get("reviews", []), top_n=3),
                "rating": place.get("rating"),
                "userRatingCount": place.get("userRatingCount"),
                "editorial_summary": place.get("editorialSummary", {}).get("text", ""),
                "primaryType": place.get("primaryType"),
                "types": place.get("types", []),
                "currentOpeningHours": place.get("currentOpeningHours", {}).get("weekdayDescriptions", [])
            }
            constructed_data.append(place_info)

        return constructed_data

    def _construct_place_details_data(self, place, origin):
        origin_lat, origin_lng = map(float, origin.split(','))
        photos = place.get("photos", [])
        photo_urls = [self._get_photo_url(photo.get("name")) for photo in photos]

        place_info = {
            "place_id": place.get("id"),
            "title": place.get("displayName", {}).get("text"),
            "location": {
                "latitude": place.get("location", {}).get("latitude"),
                "longitude": place.get("location", {}).get("longitude")
            },
            "distance": self._calculate_distance(
                origin_lat, origin_lng,
                place.get("location", {}).get("latitude"),
                place.get("location", {}).get("longitude")
            ),
            "address": place.get("formattedAddress", ""),
            "city": self._get_address_component(place, "locality"),
            "state": self._get_address_component(place, "administrative_area_level_1"),
            "country": self._get_address_component(place, "country"),
            "postal_code": self._get_address_component(place, "postal_code"),
            "photo_url": photo_urls,
            "reviews": self._get_reviews(place.get("reviews", []), top_n=10),
            "rating": place.get("rating"),
            "userRatingCount": place.get("userRatingCount"),
            "editorial_summary": place.get("editorialSummary", {}).get("text", ""),
            "primaryType": place.get("primaryType"),
            "types": place.get("types", []),
            "currentOpeningHours": place.get("currentOpeningHours", {}).get("weekdayDescriptions", []),
            "international_phone_number": place.get("internationalPhoneNumber"),
            "national_phone_number": place.get("nationalPhoneNumber"),
            "price_level": place.get("priceLevel"),
            "plus_code": place.get("plusCode", {}).get("globalCode"),
            "website_uri": place.get("websiteUri")
        }
        return place_info

    # def get_nearby_places(self, location, radius=5000, types=None):
    #     if types is None:
    #         types = ["tourist_attraction", "museum", "park"]
        
    #     def split_into_chunks(lst, n):
    #         for i in range(0, len(lst), n):
    #             yield lst[i:i + n]

    #     type_chunks = list(split_into_chunks(types, max(1, len(types) // 3)))
    #     combined_results = []

    #     headers = self._construct_map_headers()
    #     for type_chunk in type_chunks:
    #         payload = self._construct_map_nearby_search_payload(types=type_chunk, location=location, radius=radius)
    #         url = "https://places.googleapis.com/v1/places:searchNearby"
    #         response = requests.post(url, headers=headers, data=json.dumps(payload))
    #         if response.status_code == 200:
    #             combined_results += response.json().get('places', [])
    #             logger.info(f"Place chunks: {response.json().get('places', [])}")
    #         else:
    #             print(f"Error fetching data: {response.status_code}, {response.text}")
    #             return []
    #         time.sleep(0.5)

    #     # Filter (open now)
    #     combined_results = [place for place in combined_results if place.get("currentOpeningHours", {}).get("openNow", False)]
    #     # Construct
    #     combined_results = self._construct_places_data(combined_results, location)
    #     return combined_results

    def get_max_threads(self):
        return int(os.cpu_count() * 1.5)

    def _search_nearby_places_mini(self, query, location, radius=5000, num_searches=8):
        headers = self._construct_map_headers()
        payload = self._construct_map_text_search_payload(query=query, location=location, radius=radius, page_size=num_searches)
        url = "https://places.googleapis.com/v1/places:searchText"
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            results = response.json().get('places', [])
        else:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            results = []
        return self._construct_places_data(results, location)

    def get_nearby_places(self, location, radius=5000, queries=None):
        if queries is None:
            queries = ["tourist_attraction", "museum", "park"]
        
        combined_results = []
        def distribute_sum(m, n):
            base_value = m // n
            remainder = m % n
            result = [base_value] * n
            for i in range(remainder):
                result[i] += 1
            
            return result
        num_searches = distribute_sum(12, len(queries))
        for i in range(len(queries)):
            result = self._search_nearby_places_mini(queries[i], location, radius, num_searches[i])
            logger.info(f"\n\nSearch query: {queries[i]}")
            logger.info(f"result: {json.dumps([r["title"] for r in result])}")
            combined_results.extend(result)
            time.sleep(0.5)

        return combined_results

    def search_nearby_places(self, query, location, radius=5000):
        headers = self._construct_map_headers()
        payload = self._construct_map_text_search_payload(query=query, location=location, radius=radius)
        url = "https://places.googleapis.com/v1/places:searchText"

        combined_results = []
        next_page_token = None

        while len(combined_results) < 60:
            if next_page_token:
                payload['pageToken'] = next_page_token

            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                results = response.json().get('places', [])
                combined_results += results

                next_page_token = response.json().get('nextPageToken')
                if not next_page_token:
                    break
            else:
                print(f"Error fetching data: {response.status_code}, {response.text}")
                break
            time.sleep(0.5)

        combined_results = combined_results[:60]

        return self._construct_places_data(combined_results, location)

    def get_place_details(self, place_id: str, origin: str) -> dict:
        headers = self._construct_map_details_headers()
        url = f"https://places.googleapis.com/v1/places/{place_id}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            place = response.json()
            return self._construct_place_details_data(place, origin)
        else:
            print(f"Error fetching place details: {response.status_code}, {response.text}")
            return None

    def get_place_id(self, url):
        try:
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

            query_url = (
                "https://maps.googleapis.com/maps/api/place/queryautocomplete/json"
            )

            # Query parameters
            params = {
                "input": place_name,
                "types": "geocode",
                "key": {self.MAPS_API_KEY},
            }
            # Send a GET request
            response = requests.get(query_url, params=params)
            predictions = response.json()["predictions"]
            if predictions:
                place_id = predictions[0]["place_id"]
                return place_id
            else:
                return None
        except Exception as e:
            print(f"exception in get_place_id {url}", e)
            return ""
