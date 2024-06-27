import os
import csv

class DataRetriever:

    def __init__(self, upload_dir):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    def save_uploaded_file(self, file, filename):
        file_path = os.path.join(self.upload_dir, filename)
        file.save(file_path)
        return file_path

    def get_saved_places(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")

        saved_places = []

        with open(file_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                saved_places.append(
                    {
                        "Title": row.get("Title"),
                        "Note": row.get("Note"),
                        "URL": row.get("URL"),
                        "Comment": row.get("Comment"),
                    }
                )
        return saved_places

    def save_to_firestore(self, user_id, saved_places):
        doc_ref = (
            self.db.collection("users").document(user_id).collection("saved_places")
        )
        for place in saved_places:
            doc_ref.add(place)
