"""PDF extraction for CLI (standalone, no database dependencies)"""

import fitz  # PyMuPDF
import hashlib
import tiktoken
from typing import List
from dataclasses import dataclass
from .hierarchical_chunker import HybridHierarchicalChunker


@dataclass
class Chunk:
    """Simplified chunk model for CLI"""
    chunk_id: str
    text: str
    original_text: str
    source_filename: str
    page_number: int
    token_count: int


class TextNormalizer:
    """Normalize text for consistent comparison"""
    
    @staticmethod
    def normalize(text: str) -> str:
        import re
        clean_text = text.strip()
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        # Currency normalization
        clean_text = re.sub(r'\$(\d[\d,]*(?:\.\d+)?)', r'\1 USD', clean_text)
        clean_text = re.sub(r'(\d[\d,]*(?:\.\d+)?)\s*(?:usd|dollars?)\b', r'\1 USD', clean_text, flags=re.IGNORECASE)
        return clean_text


class PDFExtractor:
    """Extract and chunk PDF content using Hybrid Hierarchical chunking"""
    
    def __init__(
        self,
        max_chunk_size: int = 512,
        chunk_overlap: int = 50,
        semantic_threshold: float = 0.85,
        enable_semantic_grouping: bool = True
    ):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.chunker = HybridHierarchicalChunker(
            max_chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
            semantic_threshold=semantic_threshold,
            enable_semantic_grouping=enable_semantic_grouping
        )
    
    def process_file(self, file_path: str) -> List[Chunk]:
        """Extract chunks from a PDF file using hybrid hierarchical chunking"""
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        doc = fitz.open(stream=file_content, filetype="pdf")
        chunks = []
        
        # Collect all text from all pages first
        full_text_parts = []
        for page_num, page in enumerate(doc):
            raw_text = page.get_text()
            if raw_text.strip():
                full_text_parts.append((page_num + 1, raw_text))
        
        doc.close()
        
        # Combine pages into full document text
        # This allows header detection across page boundaries
        if not full_text_parts:
            return chunks
        
        # Process document-wide chunking
        full_document_text = "\n\n".join([text for _, text in full_text_parts])
        
        # Use hybrid hierarchical chunking
        text_segments = self.chunker.chunk(full_document_text)
        
        # Map chunks back to page numbers (approximate)
        current_page = 1
        for segment in text_segments:
            if not segment.strip():
                continue
            
            # Find which page this segment likely came from
            # Simple heuristic: check if segment appears in page text
            for page_num, page_text in full_text_parts:
                if segment[:100] in page_text or segment in page_text:
                    current_page = page_num
                    break
            
            normalized_text = TextNormalizer.normalize(segment)
            chunk_hash = hashlib.md5(normalized_text.encode()).hexdigest()
            tokens = len(self.encoder.encode(normalized_text))
            
            chunk = Chunk(
                chunk_id=chunk_hash,
                text=normalized_text,
                original_text=segment.strip(),
                source_filename=file_path,
                page_number=current_page,
                token_count=tokens
            )
            chunks.append(chunk)
        
        return chunks

