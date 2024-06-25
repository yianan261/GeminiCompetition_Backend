import os
from google.cloud import firestore

# Path to your service account key JSON file
service_account_path = "firebase_secret.json"

# Set the environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Initialize Firestore client
db = firestore.Client()


# Fetch all documents
def fetch_all_documents(collection_name: str):
    # Reference to the collection
    collection_ref = db.collection(collection_name)

    # Get all documents
    docs = collection_ref.stream()
    return list(map(lambda doc: doc.to_dict(), docs))


# Fetch the document by ID and collection name
def fetch_document_by_id(collection_name: str, document_id: str):
    # Reference to the collection
    collection_ref = db.collection(collection_name)

    # Fetch a specific document by ID
    doc = collection_ref.document(document_id).get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None


# Fetch the document by a specific field and value
def fetch_document_by_criteria(collection_name: str, field: str, value: str):
    # Reference to the collection
    collection_ref = db.collection(collection_name)

    # filter documents based on the field and value
    query = collection_ref.where(field, "==", value)

    # Get all matching documents
    docs = query.stream()

    return list(map(lambda doc: doc.to_dict(), docs))


# write to collection
def write_to_collection(collection_name: str, data: dict):
    # Reference to the collection
    collection_ref = db.collection(collection_name)

    # Add a new document with auto-generated ID
    doc_ref = collection_ref.add(data)
    return doc_ref


# write to collection with custom document id
def write_to_collection_with_id(collection_name: str, document_id: str, data: dict):
    # Reference to the collection
    collection_ref = db.collection(collection_name)

    # Set a specific document ID
    doc_ref = collection_ref.document(document_id).set(data)
    return doc_ref


# Check if document ID is present in a collection
def check_document_id_present(collection_name: str, document_id: str):
    # Reference to the collection
    collection_ref = db.collection(collection_name)

    # Fetch a specific document by ID
    doc = collection_ref.document(document_id).get()
    return doc.exists


# Delete the collection
def delete_collection(collection_name: str):
    # Reference to the collection
    collection_ref = db.collection(collection_name)

    # Get all documents
    docs = collection_ref.stream()
    for doc in docs:
        doc.reference.delete()
    return True
