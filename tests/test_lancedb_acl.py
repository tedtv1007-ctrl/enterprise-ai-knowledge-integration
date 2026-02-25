import unittest
import os
import shutil
from src.vector_service.lancedb_acl import VectorService

class TestLanceDBACL(unittest.TestCase):
    def setUp(self):
        self.db_uri = "/tmp/test_lancedb"
        if os.path.exists(self.db_uri):
            shutil.rmtree(self.db_uri)
        self.service = VectorService(self.db_uri)
        
        # Sample data
        self.data = [
            {
                "vector": [0.1, 0.2],
                "text": "HR Policy - Confidential",
                "roles": ["hr_admin"]
            },
            {
                "vector": [0.11, 0.21],
                "text": "Engineering Manual",
                "roles": ["engineer", "hr_admin"]
            },
            {
                "vector": [0.5, 0.6],
                "text": "Public Holiday List",
                "roles": ["guest", "engineer", "hr_admin"]
            }
        ]
        self.service.add_documents(self.data)

    def test_hr_admin_access(self):
        # HR Admin should see everything
        results = self.service.search([0.1, 0.2], ["hr_admin"])
        self.assertEqual(len(results), 3)

    def test_engineer_access(self):
        # Engineer should not see HR Policy
        results = self.service.search([0.1, 0.2], ["engineer"])
        self.assertEqual(len(results), 2)
        texts = results['text'].tolist()
        self.assertNotIn("HR Policy - Confidential", texts)

    def test_guest_access(self):
        # Guest should only see Public Holiday List
        results = self.service.search([0.1, 0.2], ["guest"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results.iloc[0]['text'], "Public Holiday List")

if __name__ == '__main__':
    unittest.main()
