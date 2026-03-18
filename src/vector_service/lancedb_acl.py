import lancedb
import pandas as pd
import pyarrow as pa
from typing import List, Optional, Dict, Any

class VectorService:
    def __init__(self, db_uri: str = "/tmp/lancedb_wiki"):
        self.db = lancedb.connect(db_uri)
        self.table_name = "wiki_pages"
        self._schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), 1536)), # Defaulting to common embedding size
            pa.field("text", pa.string()),
            pa.field("metadata", pa.struct([
                pa.field("path", pa.string()),
                pa.field("title", pa.string()),
                pa.field("description", pa.string()),
                pa.field("roles", pa.list_(pa.string())) # Critical for ACL
            ]))
        ])
        
    def _get_or_create_table(self):
        if self.table_name in self.db.table_names():
            return self.db.open_table(self.table_name)
        return self.db.create_table(self.table_name, schema=self._schema)

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Expects:
        {
            "id": "page_path_chunk_idx",
            "vector": [...],
            "text": "...",
            "metadata": {
                "path": "...",
                "title": "...",
                "description": "...",
                "roles": ["admin", "hr", "public"]
            }
        }
        """
        table = self._get_or_create_table()
        table.add(documents)

    def search_with_acl(self, query_vector: List[float], user_roles: List[str], limit: int = 5):
        """
        Secure search using LanceDB SQL-like filtering.
        Logic: Match if any of the user's roles are present in the record's 'roles' list.
        """
        table = self._get_or_create_table()
        
        # Construct ACL Filter: array_has_any(metadata.roles, ['role1', 'role2'])
        # Reference: LanceDB/DataFusion array functions
        roles_list_str = ", ".join([f"'{r}'" for r in user_roles])
        acl_filter = f"array_has_any(metadata.roles, [{roles_list_str}])"
        
        if not user_roles:
            acl_filter = "array_has(metadata.roles, 'public')" # Fallback to public only
            
        try:
            results = table.search(query_vector) \
                          .where(acl_filter, prefilter=True) \
                          .limit(limit) \
                          .to_pandas()
            return results
        except Exception as e:
            print(f"ACL Search Failed: {e}")
            return pd.DataFrame()

    def delete_by_path(self, path: str):
        """Clean up old versions of a page before re-indexing"""
        table = self._get_or_create_table()
        table.delete(f"metadata.path = '{path}'")
