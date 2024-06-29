import csv
from google.cloud import firestore
from datetime import datetime
from werkzeug.datastructures import FileStorage


class DataRetriever:

    def __init__(self):
        self.db = firestore.Client()

    def get_saved_places(self, files: list[FileStorage]) -> list[dict]:
        """Extracts saved places from multiple CSV files

        Args:
        files (list): list of uploaded file objects

        Returns:
        list: list of dictionaries of information of saved places

        """
        saved_places = []
        for file in files:
            file.stream.seek(0)
            reader = csv.DictReader(file.stream)
            for row in reader:
                saved_places.append(
                    {
                        "Title": row.get("Title"),
                        "Note": row.get("Note"),
                        "URL": row.get("URL"),
                        "Comment": row.get("Comment"),
                        "timestamp": datetime.now(),
                    }
                )
        return saved_places

    def save_to_firestore(self, user_id: str, saved_places: list[dict]):
        """Saves the extracted saved places to Firestore database

        Args:
        user_id (str): user id
        saved_places (list): list of dictionaries of user saved places
        """
        doc_ref = (
            self.db.collection("users").document(user_id).collection("saved_places")
        )
        for place in saved_places:
            doc_ref.add(place)
        self.remove_old_data(user_id)

    def remove_old_data(self, user_id: str):
        """Removes existing saved places for user

        Args:
        user_id (str): user id
        """
        collection_ref = (
            self.db.collection("users").document(user_id).collection("saved_places")
        )
        query_ref = collection_ref.stream()
        for doc in query_ref:
            doc.reference.delete()

    def get_most_recent_data(self, user_id: str) -> list[dict]:
        """Returns list of most recent saved places
        Args:
        user_id (str): user id

        Returns:
        list: list of dictionaries of most recent saved places
        """
        collection_ref = (
            self.db.collection("users").document(user_id).collection("saved_places")
        )
        query_ref = (
            collection_ref.order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        most_recent_data = []
        # convert document to dict
        for document in query_ref:
            most_recent_data.append(document.to_dict())

        return most_recent_data
