"""
Hybrid Hierarchical Chunking Strategy
Industry gold standard for RAG chunking.

Strategy:
1. Primary Split (Structural): Split by section headers
2. Secondary Split (Size-Based): Recursive character splitting for large sections
3. Semantic Grouping: Merge adjacent similar chunks to reduce false positives
"""

import re
import tiktoken
from typing import List, Tuple, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter


class HeaderDetector:
    """Detects section headers in PDF text (since PDFs don't have markdown)"""
    
    # Patterns that indicate section headers
    HEADER_PATTERNS = [
        # Numbered sections: "Section 1:", "Chapter 2", "1.1 Introduction"
        r'^(?:Section|Chapter|Part)\s+\d+[.:]?\s+.*',
        r'^\d+[.:]\s+.*',  # "1. Title" or "1: Title"
        r'^\d+\.\d+\s+.*',  # "1.1 Title"
        
        # All caps lines (often headers)
        r'^[A-Z][A-Z\s]{3,}$',
        
        # Lines ending with colon followed by content
        r'^[A-Z][^:]+:\s*$',
        
        # Common header keywords
        r'^(?:Introduction|Overview|Summary|Conclusion|Appendix|References?)\s*:?\s*$',
    ]
    
    @staticmethod
    def detect_headers(text: str) -> List[Tuple[int, str]]:
        """
        Detect potential section headers in text.
        Returns list of (line_index, header_text) tuples.
        """
        lines = text.split('\n')
        headers = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) < 3:
                continue
            
            # Check against patterns
            for pattern in HeaderDetector.HEADER_PATTERNS:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    headers.append((i, line_stripped))
                    break
            
            # Also check if line is short and followed by substantial content
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if (len(line_stripped) < 100 and 
                    len(next_line) > 50 and 
                    not next_line.startswith(('•', '-', '*'))):
                    # Potential header: short line followed by content
                    if line_stripped[0].isupper() and not line_stripped.endswith('.'):
                        headers.append((i, line_stripped))
        
        return headers
    
    @staticmethod
    def split_by_headers(text: str) -> List[Tuple[str, Optional[str]]]:
        """
        Split text by detected headers.
        Returns list of (section_content, header) tuples.
        """
        headers = HeaderDetector.detect_headers(text)
        
        if not headers:
            # No headers found, return entire text as one section
            return [(text, None)]
        
        lines = text.split('\n')
        sections = []
        
        # Start with content before first header
        if headers[0][0] > 0:
            pre_content = '\n'.join(lines[:headers[0][0]]).strip()
            if pre_content:
                sections.append((pre_content, None))
        
        # Process sections between headers
        for i in range(len(headers)):
            header_line_idx, header_text = headers[i]
            start_idx = header_line_idx
            
            # Find end of this section (next header or end of text)
            if i + 1 < len(headers):
                end_idx = headers[i + 1][0]
            else:
                end_idx = len(lines)
            
            # Extract section content (include header line)
            section_lines = lines[start_idx:end_idx]
            section_content = '\n'.join(section_lines).strip()
            
            if section_content:
                sections.append((section_content, header_text))
        
        return sections


class SemanticGrouper:
    """Groups adjacent chunks with high semantic similarity"""
    
    def __init__(self, similarity_threshold: float = 0.85, model_name: str = "all-MiniLM-L6-v2"):
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name
        self._embedder = None
    
    def _get_embedder(self):
        """Lazy load embedding model"""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder
    
    def group_chunks(self, chunks: List[str], encoder: tiktoken.Encoding) -> List[str]:
        """
        Merge adjacent chunks if they have high semantic similarity.
        This reduces false positive conflicts by keeping related content together.
        """
        if len(chunks) < 2:
            return chunks
        
        embedder = self._get_embedder()
        grouped = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            merged = False
            
            # Check if we can merge with next chunk
            if i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                
                # Compute similarity
                embeddings = embedder.encode([current_chunk, next_chunk], normalize_embeddings=True)
                similarity = float(embeddings[0] @ embeddings[1])
                
                # Check token limit (don't merge if combined > 1024 tokens)
                combined_text = current_chunk + "\n\n" + next_chunk
                combined_tokens = len(encoder.encode(combined_text))
                
                if similarity >= self.similarity_threshold and combined_tokens <= 1024:
                    # Merge chunks
                    grouped.append(combined_text)
                    i += 2  # Skip next chunk since we merged it
                    merged = True
            
            if not merged:
                grouped.append(current_chunk)
                i += 1
        
        return grouped


class HybridHierarchicalChunker:
    """
    Industry gold standard chunking strategy for RAG.
    
    Process:
    1. Primary Split: Split by section headers (structural)
    2. Secondary Split: Recursive character splitting for large sections (>512 tokens)
    3. Semantic Grouping: Merge adjacent similar chunks (>0.85 similarity)
    """
    
    def __init__(
        self,
        max_chunk_size: int = 512,
        chunk_overlap: int = 50,
        semantic_threshold: float = 0.85,
        enable_semantic_grouping: bool = True
    ):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_semantic_grouping = enable_semantic_grouping
        
        # Initialize recursive splitter for secondary splitting
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=lambda text: len(self.encoder.encode(text)),
            separators=["\n\n", "\n", ". ", " ", ""],  # Priority order
        )
        
        # Initialize semantic grouper
        if enable_semantic_grouping:
            self.semantic_grouper = SemanticGrouper(similarity_threshold=semantic_threshold)
        else:
            self.semantic_grouper = None
    
    def chunk(self, text: str) -> List[str]:
        """
        Main chunking method implementing hybrid hierarchical strategy.
        
        Args:
            text: Raw text to chunk
            
        Returns:
            List of chunked text segments
        """
        if not text.strip():
            return []
        
        # Step 1: Primary Split by Headers (Structural)
        sections = HeaderDetector.split_by_headers(text)
        
        all_chunks = []
        
        for section_content, header in sections:
            # Count tokens for this section
            tokens = len(self.encoder.encode(section_content))
            
            # Step 2: Secondary Split if section is too large
            if tokens > self.max_chunk_size:
                # Use recursive character splitter
                sub_chunks = self.recursive_splitter.split_text(section_content)
                all_chunks.extend(sub_chunks)
            else:
                # Section is small enough, keep as-is
                all_chunks.append(section_content)
        
        # Step 3: Semantic Grouping (merge adjacent similar chunks)
        if self.semantic_grouper and len(all_chunks) > 1:
            all_chunks = self.semantic_grouper.group_chunks(all_chunks, self.encoder)
        
        return all_chunks

