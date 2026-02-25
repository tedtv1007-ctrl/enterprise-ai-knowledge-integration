import lancedb
import pandas as pd
from typing import List, Optional

class VectorService:
    def __init__(self, db_uri: str = "/tmp/lancedb"):
        self.db = lancedb.connect(db_uri)
        self.table_name = "wiki_pages"
        
    def _get_or_create_table(self):
        if self.table_name in self.db.table_names():
            return self.db.open_table(self.table_name)
        
        # Initial schema definition (simplified)
        # In a real scenario, this would be more robust
        return None

    def add_documents(self, documents: List[dict]):
        """
        documents: List of dicts with 'vector', 'text', 'metadata'
        metadata should include 'roles' (list of roles allowed to access)
        """
        if self.table_name not in self.db.table_names():
            self.db.create_table(self.table_name, data=documents)
        else:
            table = self.db.open_table(self.table_name)
            table.add(documents)

    def search(self, query_vector: List[float], user_roles: List[str], limit: int = 5):
        table = self.db.open_table(self.table_name)
        
        # LanceDB SQL-like filter for ACL
        # metadata.roles is expected to be a list or we use a simplified string matching
        # For simplicity in this implementation, we assume roles is a string or we use 'IN' if supported
        # LanceDB supports SQL filters: https://lancedb.github.io/lancedb/sql/
        
        role_filter = " OR ".join([f"'{role}' IN (roles)" for role in user_roles])
        if not role_filter:
            role_filter = "false" # No roles, no access
            
        return table.search(query_vector).where(role_filter).limit(limit).to_pandas()
