import re
from typing import List

class ContentProcessor:
    @staticmethod
    def chunk_markdown(content: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
        """
        Advanced markdown chunking logic:
        1. Split by double newlines (paragraphs/headers)
        2. Group into chunks that stay under chunk_size
        3. Maintain overlap for context continuity
        """
        # Remove multiple newlines and normalize whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Initial split by potential section boundaries
        raw_fragments = re.split(r'(\n#{1,6}\s.*?\n)', content) # Split by markdown headers
        
        processed_fragments = []
        for frag in raw_fragments:
             if frag.strip():
                 # Further split large paragraphs by double newline
                 sub_frags = frag.split('\n\n')
                 processed_fragments.extend([f.strip() for f in sub_frags if f.strip()])

        chunks = []
        current_chunk = ""
        
        for frag in processed_fragments:
            if len(current_chunk) + len(frag) + 2 <= chunk_size:
                current_chunk += (frag + "\n\n")
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Handle fragments larger than chunk_size by hard slicing
                if len(frag) > chunk_size:
                    for i in range(0, len(frag), chunk_size - overlap):
                        chunks.append(frag[i:i + chunk_size].strip())
                    current_chunk = "" # Large frag handled, start fresh
                else:
                    current_chunk = frag + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    @staticmethod
    def clean_text(text: str) -> str:
        # Remove markdown link syntax [text](url) -> text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # Remove bold/italic markers
        text = re.sub(r'(\*\*|__|[\*_])', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
