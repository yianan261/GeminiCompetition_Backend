import os
import csv
from google.cloud import firestore
from werkzeug.datastructures import FileStorage
from datetime import datetime
from data_retriever import DataRetriever


class CSVUploader:
    """
    Handles the uploading and processing of CSV files from Google Takeout,
    and saving the extracted data to Firestore database.
    """

    def __init__(self, data_retriever: DataRetriever):
        self.data_retriever = data_retriever

    def save_uploaded_files(self, files: list[FileStorage], user_id: str) -> bool:
        """
        Processes and saves the uploaded CSV files to the 'saved_places' collection in Firestore.

        Args:
            files (list[FileStorage]): List of uploaded CSV file objects
            user_id (str): user id

        Returns:
            bool: True if the files were processed and saved successfully
        """
        saved_places = []
        try:
            for file in files:
                file.stream.seek(0)
                reader = csv.DictReader(file.stream)
                for row in reader:
                    saved_place = {
                        "user_id": user_id,
                        "title": row.get("Title"),
                        "note": row.get("Note"),
                        "url": row.get("URL"),
                        "comment": row.get("Comment"),
                        "timestamp": datetime.now(),
                    }
                    saved_places.append(saved_place)
            self.data_retriever.write_multiple_to_collection(
                "saved_places", saved_places
            )
            return True, None
        except Exception as e:
            print(f"Error processing CSV files: {e}")
            return False, str(e)
