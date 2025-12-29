"""Duplicate detection for CLI (standalone, in-memory only)"""

import os
import hashlib
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
import numpy as np


@dataclass
class DuplicateMatch:
    """Represents a duplicate match between chunks"""
    file_a: str
    file_b: str
    chunk_a_id: str
    chunk_b_id: str
    similarity: float
    chunk_a_preview: str
    chunk_b_preview: str
    type: str  # "EXACT_DUPLICATE" or "NEAR_DUPLICATE"
    
    # Additional metadata for conflict detection
    chunk_a_hash: str = ""
    chunk_b_hash: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "file_a": self.file_a,
            "file_b": self.file_b,
            "chunk_a_id": self.chunk_a_id,
            "chunk_b_id": self.chunk_b_id,
            "similarity": round(self.similarity, 4),
            "type": self.type,
            "chunk_a_preview": self.chunk_a_preview[:200],
            "chunk_b_preview": self.chunk_b_preview[:200],
        }


class Deduplicator:
    """
    In-memory duplicate detector using sentence transformers.
    
    Features:
    - Content hash for exact duplicates (fast O(1) lookup)
    - Semantic embeddings for near duplicates
    - Caching for repeated comparisons
    - Optimized cross-file comparison only
    """
    
    def __init__(
        self, 
        exact_threshold: float = 1.0, 
        near_threshold: float = 0.90,
        model_name: Optional[str] = None
    ):
        self.exact_threshold = exact_threshold
        self.near_threshold = near_threshold
        self.model_name = model_name or os.getenv("CHUNKOPS_MODEL", "all-MiniLM-L6-v2")
        
        self._embedder = None
        self._embeddings_cache: Dict[str, np.ndarray] = {}
        self._hash_cache: Dict[str, str] = {}
    
    def _get_embedder(self):
        """Lazy load the embedding model"""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.model_name)
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load model '{self.model_name}': {e}")
        return self._embedder
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent hashing"""
        # Remove extra whitespace, lowercase
        normalized = " ".join(text.lower().split())
        return normalized
    
    def _compute_hash(self, text: str) -> str:
        """Compute content hash for exact matching"""
        cache_key = id(text)
        if cache_key in self._hash_cache:
            return self._hash_cache[cache_key]
        
        normalized = self._normalize_text(text)
        hash_val = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        self._hash_cache[cache_key] = hash_val
        return hash_val
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text (cached)"""
        text_hash = self._compute_hash(text)
        
        if text_hash in self._embeddings_cache:
            return self._embeddings_cache[text_hash]
        
        embedder = self._get_embedder()
        embedding = embedder.encode(text, normalize_embeddings=True)
        embedding_arr = np.array(embedding)
        
        self._embeddings_cache[text_hash] = embedding_arr
        return embedding_arr
    
    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts"""
        emb_a = self.get_embedding(text_a)
        emb_b = self.get_embedding(text_b)
        
        # Cosine similarity = dot product of normalized vectors
        similarity = float(np.dot(emb_a, emb_b))
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    def find_duplicates(
        self, 
        chunks: List,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[DuplicateMatch]:
        """
        Find duplicates among chunks.
        
        Two-stage approach:
        1. Hash-based exact duplicate detection (O(n))
        2. Embedding-based near duplicate detection (O(n²) but cross-file only)
        
        Args:
            chunks: List of Chunk objects with text, chunk_id, source_filename
            progress_callback: Optional callback(current, total) for progress
        
        Returns:
            List of DuplicateMatch objects
        """
        duplicates: List[DuplicateMatch] = []
        
        if not chunks:
            return duplicates
        
        # =====================================================================
        # STAGE 1: Hash-based exact duplicates (fast)
        # =====================================================================
        
        hash_to_chunk: Dict[str, List] = {}
        
        for chunk in chunks:
            chunk_hash = self._compute_hash(chunk.text)
            if chunk_hash not in hash_to_chunk:
                hash_to_chunk[chunk_hash] = []
            hash_to_chunk[chunk_hash].append(chunk)
        
        # Find exact duplicates (same hash, different files)
        for hash_val, chunk_group in hash_to_chunk.items():
            if len(chunk_group) > 1:
                # Check for cross-file duplicates
                for i, chunk_a in enumerate(chunk_group):
                    for chunk_b in chunk_group[i + 1:]:
                        if chunk_a.source_filename != chunk_b.source_filename:
                            duplicates.append(DuplicateMatch(
                                file_a=chunk_a.source_filename,
                                file_b=chunk_b.source_filename,
                                chunk_a_id=chunk_a.chunk_id,
                                chunk_b_id=chunk_b.chunk_id,
                                similarity=1.0,
                                chunk_a_preview=chunk_a.text[:300],
                                chunk_b_preview=chunk_b.text[:300],
                                type="EXACT_DUPLICATE",
                                chunk_a_hash=hash_val,
                                chunk_b_hash=hash_val,
                            ))
        
        # =====================================================================
        # STAGE 2: Semantic near duplicates (cross-file comparison)
        # =====================================================================
        
        # Group chunks by file
        chunks_by_file: Dict[str, List] = {}
        for chunk in chunks:
            if chunk.source_filename not in chunks_by_file:
                chunks_by_file[chunk.source_filename] = []
            chunks_by_file[chunk.source_filename].append(chunk)
        
        files = list(chunks_by_file.keys())
        
        # Pre-compute embeddings for all chunks
        all_embeddings: Dict[str, np.ndarray] = {}
        for chunk in chunks:
            all_embeddings[chunk.chunk_id] = self.get_embedding(chunk.text)
        
        # Track already-found exact duplicates to avoid re-reporting
        exact_pairs = set()
        for dup in duplicates:
            pair_key = tuple(sorted([dup.chunk_a_id, dup.chunk_b_id]))
            exact_pairs.add(pair_key)
        
        # Count total comparisons for progress
        total_comparisons = 0
        for i, file_a in enumerate(files):
            for file_b in files[i + 1:]:
                total_comparisons += len(chunks_by_file[file_a]) * len(chunks_by_file[file_b])
        
        current_comparison = 0
        
        # Compare chunks across different files
        for i, file_a in enumerate(files):
            for file_b in files[i + 1:]:
                for chunk_a in chunks_by_file[file_a]:
                    for chunk_b in chunks_by_file[file_b]:
                        current_comparison += 1
                        
                        if progress_callback and current_comparison % 100 == 0:
                            progress_callback(current_comparison, total_comparisons)
                        
                        # Skip if already found as exact duplicate
                        pair_key = tuple(sorted([chunk_a.chunk_id, chunk_b.chunk_id]))
                        if pair_key in exact_pairs:
                            continue
                        
                        # Compute similarity using cached embeddings
                        emb_a = all_embeddings[chunk_a.chunk_id]
                        emb_b = all_embeddings[chunk_b.chunk_id]
                        similarity = float(np.dot(emb_a, emb_b))
                        
                        if similarity >= self.exact_threshold:
                            duplicates.append(DuplicateMatch(
                                file_a=chunk_a.source_filename,
                                file_b=chunk_b.source_filename,
                                chunk_a_id=chunk_a.chunk_id,
                                chunk_b_id=chunk_b.chunk_id,
                                similarity=similarity,
                                chunk_a_preview=chunk_a.text[:300],
                                chunk_b_preview=chunk_b.text[:300],
                                type="EXACT_DUPLICATE",
                                chunk_a_hash=self._compute_hash(chunk_a.text),
                                chunk_b_hash=self._compute_hash(chunk_b.text),
                            ))
                        elif similarity >= self.near_threshold:
                            duplicates.append(DuplicateMatch(
                                file_a=chunk_a.source_filename,
                                file_b=chunk_b.source_filename,
                                chunk_a_id=chunk_a.chunk_id,
                                chunk_b_id=chunk_b.chunk_id,
                                similarity=similarity,
                                chunk_a_preview=chunk_a.text[:300],
                                chunk_b_preview=chunk_b.text[:300],
                                type="NEAR_DUPLICATE",
                                chunk_a_hash=self._compute_hash(chunk_a.text),
                                chunk_b_hash=self._compute_hash(chunk_b.text),
                            ))
        
        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x.similarity, reverse=True)
        
        return duplicates
    
    def clear_cache(self):
        """Clear all caches"""
        self._embeddings_cache.clear()
        self._hash_cache.clear()
