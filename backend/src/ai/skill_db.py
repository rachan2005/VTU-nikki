"""VTU Skills Database with vector similarity search"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from config import (
    SKILLS_DATABASE_PATH,
    SKILLS_EMBEDDINGS_PATH,
    SKILLS_INDEX_PATH,
    SKILL_MATCH_THRESHOLD
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SkillDatabase:
    """
    VTU Skills database with vector similarity search.

    Uses sentence transformers for embeddings and FAISS for fast retrieval.
    Falls back to fuzzy string matching if embedding libraries unavailable.
    """

    def __init__(self, force_rebuild: bool = False):
        """
        Initialize skill database.

        Args:
            force_rebuild: Rebuild embeddings even if cache exists
        """
        # Load skills from JSON
        if not SKILLS_DATABASE_PATH.exists():
            raise FileNotFoundError(f"Skills database not found: {SKILLS_DATABASE_PATH}")

        with open(SKILLS_DATABASE_PATH) as f:
            self.skills = json.load(f)

        logger.info(f"Loaded {len(self.skills)} VTU skills")

        self.model = None
        self.embeddings = None
        self.index = None

        # Try to use vector search
        if SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE:
            self._init_vector_search(force_rebuild)
        else:
            logger.warning(
                "Vector search unavailable (missing sentence-transformers or faiss-cpu). "
                "Using fallback fuzzy matching."
            )

    def _init_vector_search(self, force_rebuild: bool):
        """Initialize vector search with embeddings"""
        # Load model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Loaded sentence transformer model")

        # Check if cache exists
        if not force_rebuild and SKILLS_EMBEDDINGS_PATH.exists() and SKILLS_INDEX_PATH.exists():
            logger.info("Loading cached embeddings and index")
            self.embeddings = np.load(SKILLS_EMBEDDINGS_PATH)
            self.index = faiss.read_index(str(SKILLS_INDEX_PATH))
        else:
            logger.info("Building embeddings and FAISS index...")
            self._build_index()

    def _build_index(self):
        """Build embeddings and FAISS index"""
        # Create text representations for each skill
        skill_texts = []
        for skill in self.skills:
            # Combine name and keywords for better matching
            text = f"{skill['name']} {' '.join(skill.get('keywords', []))}"
            skill_texts.append(text)

        # Generate embeddings
        logger.info(f"Encoding {len(skill_texts)} skills...")
        self.embeddings = self.model.encode(skill_texts, show_progress_bar=True)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)

        # Build FAISS index (using Inner Product for normalized vectors = cosine sim)
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)

        # Save to cache
        SKILLS_EMBEDDINGS_PATH.parent.mkdir(exist_ok=True)
        np.save(SKILLS_EMBEDDINGS_PATH, self.embeddings)
        faiss.write_index(self.index, str(SKILLS_INDEX_PATH))

        logger.info("Embeddings and index built and cached")

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = SKILL_MATCH_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """
        Search for skills matching query.

        Args:
            query: Search query (e.g., "python machine learning")
            top_k: Number of top results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of skill dicts with 'similarity' scores
        """
        if self.model and self.index:
            return self._vector_search(query, top_k, threshold)
        else:
            return self._fallback_search(query, top_k)

    def _vector_search(
        self,
        query: str,
        top_k: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        # Encode query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)

        # Search
        scores, indices = self.index.search(query_embedding, top_k)

        # Filter and format results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold:
                skill = self.skills[idx].copy()
                skill["similarity"] = float(score)
                results.append(skill)

        logger.debug(f"Vector search for '{query}': {len(results)} results above threshold")

        return results

    def _fallback_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback fuzzy string matching"""
        try:
            from rapidfuzz import fuzz
        except ImportError:
            logger.warning("rapidfuzz not available, using simple substring matching")
            return self._simple_substring_search(query, top_k)

        query_lower = query.lower()
        scores = []

        for skill in self.skills:
            # Combine name and keywords
            searchable = f"{skill['name']} {' '.join(skill.get('keywords', []))}".lower()

            # Calculate fuzzy match score
            score = fuzz.partial_ratio(query_lower, searchable) / 100.0
            scores.append(score)

        # Get top_k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.3:  # Threshold for fuzzy matching
                skill = self.skills[idx].copy()
                skill["similarity"] = scores[idx]
                results.append(skill)

        return results

    def _simple_substring_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Simple substring matching fallback"""
        query_lower = query.lower()
        matches = []

        for skill in self.skills:
            searchable = f"{skill['name']} {' '.join(skill.get('keywords', []))}".lower()

            if query_lower in searchable:
                skill_copy = skill.copy()
                skill_copy["similarity"] = 0.7  # Fixed score for substring match
                matches.append(skill_copy)

        return matches[:top_k]

    def get_skill_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get skill by exact name"""
        for skill in self.skills:
            if skill["name"].lower() == name.lower():
                return skill
        return None

    def get_all_skill_names(self) -> List[str]:
        """Get list of all skill names"""
        return [skill["name"] for skill in self.skills]

    def match_keywords_to_skills(
        self,
        keywords: List[str],
        max_skills: int = 5
    ) -> List[str]:
        """
        Match multiple keywords to skills and return unique skill names.

        Args:
            keywords: List of keyword strings
            max_skills: Maximum number of skills to return

        Returns:
            List of skill names (deduplicated)
        """
        all_matches = []

        for keyword in keywords:
            matches = self.search(keyword, top_k=3)
            all_matches.extend(matches)

        # Deduplicate by name, keeping highest similarity
        seen = {}
        for match in all_matches:
            name = match["name"]
            if name not in seen or match["similarity"] > seen[name]["similarity"]:
                seen[name] = match

        # Sort by similarity and take top N
        sorted_skills = sorted(seen.values(), key=lambda x: x["similarity"], reverse=True)
        return [skill["name"] for skill in sorted_skills[:max_skills]]
