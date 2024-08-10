import os
import re
import json
import time
import random
from data_retriever import DataRetriever
import google.generativeai as genai
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from cleantext import clean

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def clean_text(text):
    text = " ".join(text.strip().split())
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\W+', ' ', text)
    return clean(text)

class LLMTools:

    MODEL_ID = "gemini-1.5-pro-001"
    POSSIBLE_PLACE_TYPES = [
        "amusement_center", "amusement_park", "aquarium", "art_gallery", "athletic_field",
        "bakery", "banquet_hall", "bar", "barbecue_restaurant", "book_store", "bowling_alley",
        "breakfast_restaurant", "brunch_restaurant", "cafe", "campground", "camping_cabin",
        "casino", "chinese_restaurant", "church", "city_hall", "clothing_store", "coffee_shop",
        "convention_center", "cultural_center", "department_store", "electronics_store",
        "extended_stay_hotel", "farm", "farmstay", "ferry_terminal", "florist",
        "french_restaurant", "gift_shop", "golf_course", "hiking_area", "historical_landmark",
        "hindu_temple", "hotel", "ice_cream_shop", "indian_restaurant", "indonesian_restaurant",
        "italian_restaurant", "japanese_restaurant", "jewelry_store", "korean_restaurant",
        "lebanese_restaurant", "library", "liquor_store", "lodging", "market", "marina",
        "mediterranean_restaurant", "mexican_restaurant", "middle_eastern_restaurant", "mosque",
        "movie_theater", "museum", "national_park", "night_club", "park", "performing_arts_theater",
        "pizza_restaurant", "ramen_restaurant", "resort_hotel", "restaurant", "sandwich_shop",
        "school", "seafood_restaurant", "shopping_mall", "shoe_store", "ski_resort", "spa",
        "sports_club", "sports_complex", "stadium", "steak_house", "swimming_pool",
        "thai_restaurant", "tourist_attraction", "turkish_restaurant", "university",
        "vegan_restaurant", "vegetarian_restaurant", "visitor_center", "vietnamese_restaurant",
        "wedding_venue", "zoo"
    ]
    SAVED_PLACES_LIMIT = 50

    def __init__(self, data_retriever: DataRetriever):
        self.data_retriever = data_retriever
        with open(os.getenv("GOOGLE_KEY")) as f:
            keys = json.load(f)
            os.environ["GOOGLE_API_KEY"] = keys["GOOGLE_API_KEY"]
            os.environ["GOOGLE_CSE_ID"] = keys["GOOGLE_CSE_ID"]
            self.GEMINI_API_KEY = keys["GEMINI_API_KEY"]
        genai.configure(api_key=self.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.MODEL_ID)

    def test_api(self):
        response = self.model.generate_content("Write a story about an AI")
        return response.text

    def _call_llm(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _get_relevant_user_info(self, email: str, limit: int, include_description: bool):

        relevant_info = {}
        # Visited places (get half restaurants half non restaurants since most visited places are restaurants)
        visited_places = self.data_retriever.fetch_document_by_criteria("saved_places", "user_email", email)
        visited_places_other_than_restaurants = [visit for visit in visited_places if "food" not in visit.get("types", []) and "restaurant" not in visit.get("types", [])]
        visited_places_other_than_restaurants = [
            {
                "title": place.get("title", ""),
                "types": place.get("types", []),
                "note": place.get("note", ""),
                "place_description": place.get("place_description", ""),
                "comment": place.get("comment", "")
            } for place in visited_places_other_than_restaurants
        ]
        if len(visited_places_other_than_restaurants) > limit // 2:
            visited_places_other_than_restaurants = random.sample(visited_places_other_than_restaurants, limit // 2)

        visited_places_restaurants = [visit for visit in visited_places if "food" in visit.get("types", []) or "restaurant" in visit.get("types", [])]
        visited_places_restaurants = [
            {
                "title": place.get("title", ""),
                "types": place.get("types", []),
                "note": place.get("note", ""),
                "place_description": place.get("place_description", ""),
                "comment": place.get("comment", "")
            } for place in visited_places_restaurants
        ]
        if len(visited_places_restaurants) > limit // 2:
            visited_places_restaurants = random.sample(visited_places_restaurants, limit // 2)

        visited_place_combined = visited_places_other_than_restaurants + visited_places_restaurants
        def custom_serializer(obj):
            if isinstance(obj, DatetimeWithNanoseconds):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        visited_place_combined_str = json.dumps({"visited places": visited_place_combined}, default=custom_serializer)
        relevant_info["visited_places"] = visited_place_combined_str

        # Interests
        user_data = self.data_retriever.fetch_document_by_id("users", email)
        interests = user_data.get("interests", [])
        interests_str = json.dumps({"interests": interests})
        relevant_info["interests"] = interests_str

        if include_description:
            relevant_info["userDescription"] = user_data.get("userDescription", "")
            relevant_info["geminiDescription"] = user_data.get("geminiDescription", "")

        return relevant_info

    def _construct_relevant_fields_from_places_data(self, places_data: list):
        return [
            {
                "place_id": place.get("place_id", ""),
                "title": place.get("title", ""),
                "editorial_summary": place.get("editorial_summary", ""),
                "reviews": [
                    {
                        "rating": review.get("rating"),
                        "text": review.get("text")
                    } for review in place.get("reviews", [])
                ],
                "primary_type": place.get("primaryType", ""),
                "types": place.get("types", []),
                "overall_ratings": place.get("rating"),
                "user_rating_count": place.get("userRatingCount")
            } for place in places_data
        ]

    def _construct_relevant_fields_from_place_details_data(self, place_data: dict):
        return {
            "title": place_data.get("title", ""),
            "summary": place_data.get("editorial_summary", ""),
            "primary_type": place_data.get("primaryType", ""),
            "types": place_data.get("types", []),
            "overall_rating": place_data.get("rating"),
            "user_rating_count": place_data.get("userRatingCount"),
            "reviews": [
                {
                    "text": review.get("text", ""),
                    "rating": review.get("rating")
                } for review in place_data.get("reviews", [])
            ][:5],
            "price_level": place_data.get("price_level", ""),
            "website_uri": place_data.get("website_uri")
        }


    def generate_user_description(self, email: str):
        # Visited places data
        user_info = self._get_relevant_user_info(email=email, limit=self.SAVED_PLACES_LIMIT, include_description=False)
        user_visited_places = user_info.get("visited_places", "{}")
        user_interests = user_info.get("interests", "{}")
        user_description = user_info.get("userDescription", "")
        if len(json.loads(user_interests).get("interests", [])) == 0 and len(json.loads(user_visited_places).get("visited_places", [])) == 0 and not user_description:
            return "Hi, there is not enough information about you. Please add a brief description about your preferences below!"

        PROMPT = f"""
        You are an AI assistant for the places recommendation app. This app gives the user some place recommendations based on the user's preference.
        
        Your job is to create a short story (1 paragraph) about the user. The story needs to be based on the user's data such as user's previous visited places and user's interests.
        
        The story needs to be like a description about the user, so it should use the word "you" as you'll be writing directly to the user. You also need to use adjective for example like “adventurous,” “explorative,”, “culinary-enthusiastic”, or anything else that you see fit. 
        
        And as you might know, people go to restaurants a lot, while you can describe about the user's taste, you also need to be focus more on the other places that might interests users other than just restaurants.
        
        Here's the user's previously visited places in a JSON format (if available):
        {user_visited_places}
        
        You have to analyze the visited place above and notice which places that are relevant for the app and which one are not. The places that are relevant are like museum, park, restaurants, or other fun places. The places that are not relevant to our app are like the office, user's house, or the non-attraction places. From the visited places above, you have to get the idea of what the user's preferences are to be written as a story or description.
        
        Here's the user's interests in a JSON format (if available):
        {user_interests}

        Here's the user's personal description about themselves (if empty, the user doesn't provide description): {user_description}
        
        For your reference, here is a list of possible type places. Feel free to use this in the story or description that you generated (you need to correct the spelling like changing _ to space though).
        
        Please add a brief description about your preferences below!"

        Now, combining the visited places and interests, generate a short story or description about the user. The answer must only be the short story or description about the user, don't give explanation or other thing. Despite the lack of user data and you can't think of any personalized description for the user, you still have to give generic description that applies to most users.
        """
        
        return self._call_llm(PROMPT)

    def generate_place_types(self, email: str) -> list:
        user_info = self._get_relevant_user_info(email=email, limit=self.SAVED_PLACES_LIMIT, include_description=True)

        # Prepare the prompt
        PROMPT = f"""
        You are an AI assistant for a places recommendation app. This app gives the user some place recommendations based on the user's preferences.
        
        Here are the user's details:
            User Description: {user_info["userDescription"]}
            Gemini Description: {user_info["geminiDescription"]}
            Interests: {user_info["interests"]}
        
        The following are some places the user has visited:
        {user_info["visited_places"]}
        
        Based on the user's description, gemini description, interests, and visited places, identify the most relevant types of places for this user from the following list:
        {', '.join(self.POSSIBLE_PLACE_TYPES)}

        The maximum place types that you can think of is nine (9) types. So think of the nine most relevant types based on the user data.

        Other than that, you can also predict which place types that might be relevant to the user as well. So based on the user's data, try to guess the place types from the list of possible place types which might interests the user.

        Return only the types of places that are most relevant to the user, separated by commas.
        
        For example: convention_center, department_store, farm, ferry_terminal, food, french_restaurant, gift_shop
        
        Do not provide explanations at all, just the answer seperated by commas.
        """

        # Call the LLM to generate the filtered place types (three tries)
        for i in range(3):
            response = self._call_llm(PROMPT)
            filtered_place_types = [place_type.strip() for place_type in response.split(",") if place_type.strip()]
            filtered_place_types = [place for place in filtered_place_types if place in self.POSSIBLE_PLACE_TYPES]
            if len(filtered_place_types) > 0:
                break

        recommended_types_from_kelvin = ["tourist_attraction", "museum", "park"]
        filtered_place_types += recommended_types_from_kelvin
        filtered_place_types = list(set(filtered_place_types))

        return filtered_place_types

    def filter_relevant_places(self, email: str, places: list, weather: str) -> list:
        user_info = self._get_relevant_user_info(email=email, limit=self.SAVED_PLACES_LIMIT, include_description=True)
        places_json = json.dumps(self._construct_relevant_fields_from_places_data(places_data=places))
        
        PROMPT = f"""
        You are an AI assistant for a places recommendation app. This app gives the user some place recommendations based on the user's preferences.

        Here are the user's details:
            User Description: {user_info["userDescription"]}
            Gemini Description: {user_info["geminiDescription"]}
            Interests: {user_info["interests"]}
        
        Here is the current weather information: {weather}

        The following are some places the user has visited:
        {user_info["visited_places"]}

        Here are some potential places to recommend:
        {places_json}

        Based on the user's description, gemini description, interests, current weather, and visited places, identify the top 12 places that are most relevant to the user from the provided list.

        Look carefully at the potential places, there are a lot of fields to consider to make recommendation to the user. You need to consider every fields and give me top 10 places that are most likely to be enjoyable by the user. And do as best as you can to avoid selecting fast food restaurants if you're selecting a restaurant, we want the places to be unique and not fast food.

        Provide only the place IDs of the top 12 places starting from the best one, separated by commas. Do not provide any other explanations or details at all!
        """

        response = self._call_llm(PROMPT)
        filtered_place_ids = [place_id.strip() for place_id in response.strip().split(",") if place_id.strip()]
        filtered_places = [place for place in places if place["place_id"] in filtered_place_ids]
        return filtered_places


    def parse_query_for_search(self, query: str):
        PROMPT = f"""
        You are an AI assistant for a places recommendation app. This app gives the user some place recommendations based on the user's query.

        Your job is to determine if the user's query is suitable for a text search or a nearby search API from google places API.
        
        If the query contains specific details like a restaurant name, cuisine type, or any specific type of place, it should be a text search. Otherwise, it should be a nearby search.

        Here's a bit of explanation of the text search API:
        
        A Text Search (New) returns information about a set of places based on a string — for example "pizza in New York" or "shoe stores near Ottawa" or "123 Main Street". The service responds with a list of places matching the text string and any location bias that has been set. The service is especially useful for making ambiguous address queries in an automated system, and non-address components of the string may match businesses as well as addresses. Examples of ambiguous address queries are poorly-formatted addresses or requests that include non-address components such as business names. Requests like the first two examples in the following table may return zero results unless a location — such as region, location restriction, or location bias — is set.

        Respond with a python dictionary object that includes:
        - "use_text_search": true or false
        - "text_query": the query to be used for the text search (if applicable)
        - "types": a list of place types to be used for the nearby search (if applicable)

        The text_query field might not be clear from the user's query. So you have to think about what the user really wants from the user's query and what should you type on the text_query so that the google text search API can work.

        If the nearby search API is more appropriate (since we can specify types), the "types" variables need to be taken from the following list: [{', '.join(self.POSSIBLE_PLACE_TYPES)}]

        Note that for the use_text_search equals false, the types needs to be contains in the list above, do not use types other than the one listed above.

        Example 1:
        If the user's query is: "I'm hungry, I want to eat mexican food near me, possibly with chicken.
        
        You answer:
        {{
            "use_text_search": true,
            "text_query": "Mexican food with chicken"
        }}

        Example 2:
        If the user's query is: I'm tired but I still want to hang out.
        
        You answer:
        {{
            "use_text_search": false,
            "types": ["coffee_shop", "spa", "movie_theater"]
        }}
        
        Example 3:
        If the user's query is: I want to hike.
        
        You can answer:
        {{
            "use_text_search": false,
            "types": ["hiking_area", "national_park"
        }}
        
        or you can answer:
        {{
            "use_text_search": true,
            "text_query": "Hiking area near me"
        }}
        
        Example 4:
        If the user's query is: Bubble tea
        
        You can answer:
        {{
            "use_text_search": true,
            "text_query": "Bubble tea"
        }}

        Example 5:
        If the user's query is: Any good book stores around?

        You can answer:
        {{
            "use_text_search": true,
            "text_query": "book stores near me"
        }}

        or you can answer:
        {{
            "use_text_search": false,
            "types": ["library", "book_store"]
        }}

        The user has provided the following query on the app search bar:
        "{query}"

        Respond only the dictionary object (i.e. {{...}}) without any other explanations or symbol starting and ending with curly braces.
        """

        response = self._call_llm(PROMPT)
        try:
            response = response.strip()
            response_dict = json.loads(response)
            if not response_dict.get("use_text_search"):
                filtered_place_types = [place for place in response_dict.get("types", []) if place in self.POSSIBLE_PLACE_TYPES]
                response_dict["types"] = list(set(filtered_place_types))
            return response_dict
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print("Response text that caused the error:", response)
            return None


    def filter_relevant_places_based_on_query(self, query: str, email: str, places: list, weather: str) -> list:
        user_info = self._get_relevant_user_info(email=email, limit=self.SAVED_PLACES_LIMIT, include_description=True)
        places_json = json.dumps(self._construct_relevant_fields_from_places_data(places_data=places))

        PROMPT = f"""
        You are an AI assistant for a places recommendation app. This app gives the user some place recommendations based on the user's preferences and specific query.

        The user has provided the following query:
        "{query}"

        Here are the user's details:
            User Description: {user_info["userDescription"]}
            Gemini Description: {user_info["geminiDescription"]}
            Interests: {user_info["interests"]}

        Here is the current weather information: {weather}

        The following are some places the user has visited:
        {user_info["visited_places"]}

        Here are some potential places to recommend:
        {places_json}

        Based on the user's description, gemini description, interests, weather, visited places, and most importantly the user's query, identify the top 12 places that are most relevant to the user from the provided list.

        Pay special attention to the user's query to ensure the recommendations align closely with what the user is looking for. Consider every field on the potential places and ensure the recommendations are unique and align with the user's preferences.

        Provide only the place IDs of the top 12 places starting from the best one, separated by commas. Do not provide any other explanations or details at all!
        """

        response = self._call_llm(PROMPT)
        filtered_place_ids = [place_id.strip() for place_id in response.strip().split(",") if place_id.strip()]
        filtered_places = [place for place in places if place["place_id"] in filtered_place_ids]
        return filtered_places
    
    def _scrape_website(self, url):
        try:
            def custom_extractor(html_content):
                soup = BeautifulSoup(html_content, "html.parser")
                return soup.get_text()

            loader = WebBaseLoader(url)
            docs = loader.load()
            website_content = ' '.join([doc.page_content for doc in docs])
            return website_content
        except Exception as e:
            print(f"Error scraping website: {e}")
            return ""

    def _run_google_search(self, query, num_results=5):
        search = GoogleSearchAPIWrapper()
        def topn_results(query):
            return search.results(query, num_results)

        tool = Tool(
            name="Google Search Snippets",
            description="Search Google for recent results.",
            func=topn_results,
        )
        return tool.run(query)

    def process_place_details(self, email: str, place_data: dict) -> dict:
        def _get_prompt_for_content_check(additional_info: list): 
            return f"""
            You are an AI assistant for a places recommendation app. This app gives the user some place recommendations based on the user's preferences and specific query.
            
            Please check the following scraped website content from different sources to determine if this information is sufficient to provide interesting facts about the {relevant_place_data["title"]} for the user. 

            Website Content: {json.dumps(additional_info)}.

            Response with either YES or NO only.

            If the content is sufficient, respond with 'YES'. 
            Otherwise, respond with 'NO'.
            Do not provide any other explanation! Only response with YES or NO string. If the website content is empty, reply with NO.
            """
        def _get_prompt_for_query(additional_info, relevant_place_data, tried_queries):
            return f"""
            You are an AI assistant for a places recommendation app. This app gives the user some place recommendations based on the user's preferences and specific query.

            You are now planning to write about the personalized interesting fact (or information if applicable) about {relevant_place_data["title"]} for the user. You have gained access about the user's preference and user's historical visited place.

            Here is the information that is available about the place: {json.dumps(relevant_place_data)}
            Here is the information that has been scraped from the website or google: {json.dumps(additional_info)}
            The queries that have been used to generate the above results (empty if we haven't use Google Search): {json.dumps(tried_queries)}

            The available content is still not sufficient to generate interesting facts (or information if this place needs information) about {relevant_place_data['title']}. 

            You have now get access to use Google Search to further extract more information. Please provide a suitable query that should be used on Google search to gather sufficient data for generating the required information. The query should be comprehensive and designed to retrieve detailed information needed to generate interesting facts (or historical information if applicable) about {relevant_place_data['title']}.
            
            Respond only with the query string for the Google Search. The query string is the human language that people usually type when doing Google Search. Do not generate the same queries that have been used as indicated above.
            """
        def _get_prompt_for_interesting_facts(additional_info, relevant_place_data, user_info):
            return f"""
            You are an AI assistant for a places recommendation app. This app gives the user some place recommendations based on the user's preferences and specific query.

            You are now planning to write about the personalized interesting fact about {relevant_place_data["title"]} for the user. You have gained access about the user's preference and user's historical visited place.
            
            Here are the user's details:
                User Description: {user_info["userDescription"]}
                Gemini Description: {user_info["geminiDescription"]}
                Interests: {user_info["interests"]}

            You have to focus on the user data since the interesting fact needs to be according to the user. Make it personalized.
            
            Here are the details about the place:
            {json.dumps(relevant_place_data)}
            
            Here are the additional informations that are scraped from the internet about the place:
            {json.dumps(additional_info)}
            
            Now generate the interesting facts about the place. The interesting facts need to be very personalized to the user so different user needs to have different interesting facts about the place.
            
            Generate one paragraph interesting facts only without any other explanation! The interesting facts need to be very personalized to show why the user will like the place! Be creative!
            """
        scrapped_urls = []
        logger.info("process_place_details() triggered")
        logger.info("process_place_details(): Fetching relevant user info...")
        user_info = self._get_relevant_user_info(email=email, limit=self.SAVED_PLACES_LIMIT, include_description=True)
        logger.info(f"process_place_details(): User info fetched: {user_info}")
        logger.info("Constructing relevant fields from place details data...")
        relevant_place_data = self._construct_relevant_fields_from_place_details_data(place_data=place_data)
        logger.info(f"process_place_details(): Relevant place data: {relevant_place_data}")
        if "website_uri" in relevant_place_data and relevant_place_data.get("website_uri"):
            logger.info(f"process_place_details(): Scraping website content from {relevant_place_data.get('website_uri')}...")
            additional_info = [
                {
                    "link": relevant_place_data.get("website_uri"),
                    "title": "",
                    "snippet": "",
                    "content": self._scrape_website(relevant_place_data["website_uri"])
                }
            ]
            scrapped_urls.append(relevant_place_data.get("website_uri"))
            logger.info("process_place_details(): Website content scraped.")
        prompt_for_content_check = _get_prompt_for_content_check(additional_info=additional_info)
        content_check_response = self._call_llm(prompt_for_content_check)
        logger.info(f"process_place_details(): Content check response: {content_check_response}")
        time.sleep(0.8)

        AGENT_ITERATION_LIMIT = 3
        i = 0
        tried_queries = []
        while content_check_response.lower() != 'yes' and i < AGENT_ITERATION_LIMIT:
            i += 1
            google_query_prompt = _get_prompt_for_query(additional_info=additional_info, relevant_place_data=relevant_place_data, tried_queries=tried_queries)
            if i == 1:
                query_string = relevant_place_data["title"]
            else:
                query_string = self._call_llm(google_query_prompt)
            tried_queries.append(query_string)
            logger.info(f"process_place_details(): Query string for Google search: {query_string}")
            time.sleep(0.8)
            search_results = self._run_google_search(query_string)
            logger.info(f"process_place_details(): Search results: {search_results}")

            # No good Google Search Result was found
            if len(search_results) == 1:
                break
            
            # Scrape content of each result
            for result in search_results:
                if result["link"] in scrapped_urls:
                    continue
                logger.info(f"process_place_details(): Scraping content from {result['link']}...")
                cleaned_content = clean_text(self._scrape_website(url=result["link"]))
                
                # TODO: Might need to use vector database rather than heuristic first 500 tokens (firestore can do vector store??)
                result["content"] = " ".join(cleaned_content.split()[:500])
                logger.info(f"process_place_details(): Scraped content: {result['content']}")
            additional_info += search_results
            prompt_for_content_check = _get_prompt_for_content_check(additional_info=additional_info)
            content_check_response = self._call_llm(prompt_for_content_check)
            logger.info(f"process_place_details(): Updated content check response: {content_check_response}")
            time.sleep(0.8)

        interesing_facts_prompt = _get_prompt_for_interesting_facts(
            additional_info=additional_info, relevant_place_data=relevant_place_data, user_info=user_info
        )
        interesting_facts = self._call_llm(interesing_facts_prompt)
        logger.info(f"process_place_details(): Interesting facts: {interesting_facts}")
        place_data["interesting_facts"] = interesting_facts
        return place_data