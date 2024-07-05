import unittest
from data_retriever import DataRetriever

from dotenv import load_dotenv

load_dotenv()

data_retriever = DataRetriever()


class TestFirebase(unittest.TestCase):

    def test_delete_collection(self):
        collection_name = "test_attractions"
        data_retriever.delete_collection(collection_name)
        result = data_retriever.fetch_all_documents(collection_name)
        self.assertTrue(len(result) == 0)

    def test_write_to_collection(self):
        collection_name = "test_attractions"
        data = {"name": "Grand Canyon", "state": "Arizona"}
        data_retriever.write_to_collection(collection_name, data)
        result = data_retriever.fetch_document_by_criteria(
            collection_name, "name", "Grand Canyon"
        )
        self.assertEqual(len(result), 1)

    def test_write_to_collection_with_id(self):
        collection_name = "test_attractions"
        data = {"name": "Grand Canyon", "state": "Arizona"}
        data_retriever.write_to_collection_with_id(
            collection_name, "Grand_canyon_arizona", data
        )
        result = data_retriever.fetch_document_by_id(
            collection_name, "Grand_canyon_arizona"
        )
        # Counting the fields in the document
        self.assertEqual(len(result), 2)

    def test_fetch_all_documents(self):
        collection_name = "test_attractions"
        result = data_retriever.fetch_all_documents(collection_name)
        self.assertEqual(len(result), 2)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestFirebase("test_delete_collection"))
    suite.addTest(TestFirebase("test_write_to_collection"))
    suite.addTest(TestFirebase("test_write_to_collection_with_id"))
    suite.addTest(TestFirebase("test_fetch_all_documents"))
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
