import os
from google.cloud import firestore


class DataRetriever:

    def __init__(self, db):
        self.db = db

    def fetch_all_documents(self, collection_name: str):
        collection_ref = self.db.collection(collection_name)

        docs = collection_ref.stream()
        return list(map(lambda doc: doc.to_dict(), docs))

    def fetch_document_by_id(self, collection_name: str, document_id: str):
        collection_ref = self.db.collection(collection_name)

        doc = collection_ref.document(document_id).get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None

    def fetch_document_by_criteria(self, collection_name: str, field: str, value: str):
        collection_ref = self.db.collection(collection_name)

        query = collection_ref.where(field, "==", value)

        docs = query.stream()

        return list(map(lambda doc: doc.to_dict(), docs))

    # write to collection
    def write_to_collection(self, collection_name: str, data: dict):
        try:
            collection_ref = self.db.collection(collection_name)

            doc_ref = collection_ref.add(data)
            return doc_ref[1].id  # return generated doc ID
        except Exception as e:
            print(f"Error writing document to collection {collection_name}: {e}")
            return None

    def write_to_collection_with_id(
        self, collection_name: str, document_id: str, data: dict
    ):
        """
        Write data to a collection with a specified document ID.

        Args:
            collection_name (str): The name of the collection.
            document_id (str): doc ID (user email)
            data (dict): The data to write to the document.

        Returns:
            str: The document ID if the write was successful.
        """
        try:
            collection_ref = self.db.collection(collection_name)

            # Set specific document ID
            doc_ref = collection_ref.document(document_id)
            doc_ref.set(data)
            return document_id
        except Exception as e:
            print(f"Error writing document to collection {collection_name}: {e}")
            return None

    def write_multiple_to_collection(
        self, collection_name: str, data: list[dict]
    ) -> bool:
        """
        Writes multiple documents to a collection using batched writes

        Args:
            collection_name (str)
            data (list[dict])

        Returns:
            bool: True if all documents written successfully
        """
        try:
            collection_ref = self.db.collection(collection_name)
            # 500 operations allowed at a time for Firestore batch writes
            batches = [data[i : i + 500] for i in range(0, len(data), 500)]

            for batch_data in batches:
                batch = self.db.batch()
                for item in batch_data:
                    doc_ref = collection_ref.document()
                    batch.set(doc_ref, item)
                batch.commit()

            return True
        except Exception as e:
            print(f"Error committing batch: {e}")
            return False

    # Checks if document ID is present in a collection
    def check_document_id_present(self, collection_name: str, document_id: str):
        collection_ref = self.db.collection(collection_name)

        doc = collection_ref.document(document_id).get()
        return doc.exists

    # Deletes the collection
    def delete_collection(self, collection_name: str):
        collection_ref = self.db.collection(collection_name)

        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        return True

    def delete_document_by_id(self, collection_name: str, document_id: str) -> bool:
        """
        Deletes specific document by ID

        Args:
            collection_name (str): Name of the collection where the document should be deleted
            document_id (str): document ID

        Returns:
            bool: True if the document is deleted successfully, else False
        """
        collection_ref = self.db.collection(collection_name)
        doc_ref = collection_ref.document(document_id)
        doc_ref.delete()
        return True

    def update_users_field(self, user_id: str, fields: dict) -> bool:
        """
        Updates specific fields in users collection

        Args:
            user_id (str): user ID
            fields (dict): The fields to update with their new values

        Returns:
            bool: True if the update was successful, else False
        """
        try:
            collection_ref = self.db.collection("users")
            doc_ref = collection_ref.document(user_id)
            doc_ref.update(fields)
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
