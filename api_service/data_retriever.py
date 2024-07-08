import os
from google.cloud import firestore


class DataRetriever:

    def __init__(self):
        self.db = firestore.Client(database="gemini-trip")

    # Fetch all documents
    def fetch_all_documents(self, collection_name: str):
        # Reference to the collection
        collection_ref = self.db.collection(collection_name)

        # Get all documents
        docs = collection_ref.stream()
        return list(map(lambda doc: doc.to_dict(), docs))

    # Fetch the document by ID and collection name
    def fetch_document_by_id(self, collection_name: str, document_id: str):
        # Reference to the collection
        collection_ref = self.db.collection(collection_name)

        # Fetch a specific document by ID
        doc = collection_ref.document(document_id).get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None

    # Fetch the document by a specific field and value
    def fetch_document_by_criteria(self, collection_name: str, field: str, value: str):
        # Reference to the collection
        collection_ref = self.db.collection(collection_name)

        # filter documents based on the field and value
        query = collection_ref.where(field, "==", value)

        # Get all matching documents
        docs = query.stream()

        return list(map(lambda doc: doc.to_dict(), docs))

    # write to collection
    def write_to_collection(self, collection_name: str, data: dict):
        # Reference to the collection
        collection_ref = self.db.collection(collection_name)

        # Add a new document with auto-generated ID
        doc_ref = collection_ref.add(data)
        return str(doc_ref)

    # write to collection with custom document id
    def write_to_collection_with_id(
        self, collection_name: str, document_id: str, data: dict
    ):
        # Reference to the collection
        collection_ref = self.db.collection(collection_name)

        # Set a specific document ID
        doc_ref = collection_ref.document(document_id).set(data)
        return str(doc_ref)

    # Check if document ID is present in a collection
    def check_document_id_present(self, collection_name: str, document_id: str):
        # Reference to the collection
        collection_ref = self.db.collection(collection_name)

        # Fetch a specific document by ID
        doc = collection_ref.document(document_id).get()
        return doc.exists

    # Delete the collection
    def delete_collection(self, collection_name: str):
        # Reference to the collection
        collection_ref = self.db.collection(collection_name)

        # Get all documents
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        return True
