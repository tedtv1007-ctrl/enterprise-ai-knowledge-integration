import psycopg2
from pgvector.psycopg2 import register_vector
import logging
import os

logger = logging.getLogger("wiki-vector-store")

class VectorStore:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql://wiki_user:wiki_password@localhost:5432/wiki_db")
        self._conn = None

    def get_conn(self):
        if self._conn is None:
            try:
                # Use a proper connection string for psycopg2
                conn_str = self.db_url
                self._conn = psycopg2.connect(conn_str)
                with self._conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                register_vector(self._conn) # Register vector type with current connection
                self._conn.commit()
                logger.info("Successfully connected to pgvector database.")
            except Exception as e:
                logger.error(f"Failed to connect to database: {str(e)}")
                raise
        return self._conn

    def create_table(self):
        with self.get_conn().cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wiki_embeddings (
                    id SERIAL PRIMARY KEY,
                    page_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT,
                    embedding vector(384),
                    UNIQUE(page_path, chunk_index)
                )
            """)
            self.get_conn().commit()
            logger.info("Database table wiki_embeddings initialized.")

    def upsert_embedding(self, page_path: str, chunk_index: int, content: str, embedding: list):
        with self.get_conn().cursor() as cur:
            cur.execute("""
                INSERT INTO wiki_embeddings (page_path, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (page_path, chunk_index) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding
            """, (page_path, chunk_index, content, embedding))
            self.get_conn().commit()

    def delete_page_embeddings(self, page_path: str):
        with self.get_conn().cursor() as cur:
            cur.execute("DELETE FROM wiki_embeddings WHERE page_path = %s", (page_path,))
            self.get_conn().commit()
