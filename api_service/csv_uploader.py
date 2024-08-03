import os
import csv
import io
from datetime import datetime
from data_retriever import DataRetriever
from zipfile import ZipFile


class CSVUploader:

    def __init__(self, data_retriever: DataRetriever):
        self.data_retriever = data_retriever

    def check_duplicate(self, user_email: str, title: str) -> bool:
        """
        Checks if a document with the same user_email and title already exists.

        Args:
            user_email (str): user email
            title (str): title of the saved place

        Returns:
            bool: True if a duplicate exists, False otherwise
        """
        existing_docs = self.data_retriever.fetch_document_by_criteria(
            "saved_places", "user_email", user_email
        )
        for doc in existing_docs:
            if doc["title"] == title:
                return True
        return False

    def process_zip_file(self, file_stream, user_email: str) -> bool:
        """
        Processes and saves the CSV files from a zip file to the 'saved_places' collection in Firestore.

        Args:
            file_stream (io.BytesIO): Stream of the zip file
            user_email (str): user email

        Returns:
            bool: True if the files were processed and saved successfully
        """
        try:
            with ZipFile(file_stream, "r") as zip_ref:
                for file_name in zip_ref.namelist():
                    if file_name.startswith("Takeout/Saved/") and file_name.endswith(
                        ".csv"
                    ):
                        with zip_ref.open(file_name) as csv_file:
                            reader = csv.DictReader(io.TextIOWrapper(csv_file, "utf-8"))
                            for row in reader:
                                title = row.get("Title")
                                if self.check_duplicate(user_email, title):
                                    continue  # Skip duplicates
                                saved_place = {
                                    "user_email": user_email,
                                    "title": title,
                                    "note": row.get("Note"),
                                    "url": row.get("URL"),
                                    "comment": row.get("Comment"),
                                    "timestamp": datetime.now(),
                                }
                                self.data_retriever.write_to_collection(
                                    "saved_places", saved_place
                                )
            return True, None
        except Exception as e:
            return False, str(e)

    def process_folder(self, folder_path: str, user_email: str) -> bool:
        """
        Processes and saves the CSV files from a folder to the 'saved_places' collection in Firestore.

        Args:
            folder_path (str): Path to the folder
            user_email (str): user email

        Returns:
            bool: True if the files were processed and saved successfully
        """
        try:
            for root, _, files in os.walk(folder_path):
                for file_name in files:
                    if file_name.endswith(".csv"):
                        with open(
                            os.path.join(root, file_name), "r", encoding="utf-8"
                        ) as csv_file:
                            reader = csv.DictReader(csv_file)
                            for row in reader:
                                title = row.get("Title")
                                if self.check_duplicate(user_email, title):
                                    continue  # Skip duplicates
                                saved_place = {
                                    "user_email": user_email,
                                    "title": title,
                                    "note": row.get("Note"),
                                    "url": row.get("URL"),
                                    "comment": row.get("Comment"),
                                    "timestamp": datetime.now(),
                                }
                                self.data_retriever.write_to_collection(
                                    "saved_places", saved_place
                                )
            return True, None
        except Exception as e:
            return False, str(e)
