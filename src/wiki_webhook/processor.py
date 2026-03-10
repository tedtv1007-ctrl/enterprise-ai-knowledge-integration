import re
from typing import List

class ContentProcessor:
    @staticmethod
    def chunk_markdown(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Simple markdown chunking logic.
        """
        # Remove some markdown noise if necessary
        # For now, just split by length with overlap
        chunks = []
        for i in range(0, len(content), chunk_size - overlap):
            chunks.append(content[i:i + chunk_size])
        return chunks

    @staticmethod
    def clean_text(text: str) -> str:
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text).strip()
        return text
