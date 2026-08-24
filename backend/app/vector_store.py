"""
Semantic layer for product search and substitution.

This is the "vector database / similarity search" piece from the spec.
We embed every product's (name + category + brand + description) text with a
sentence-transformer, index the vectors in FAISS, and use cosine similarity
(via normalized inner product) for:

  - Smart semantic search ("organic fruits below 300")
  - Product substitution ("replace regular milk" -> almond/soy/oat milk)

No hardcoded substitute tables anywhere - the "substitutes" for a product are
just whatever the FAISS index says is nearest in embedding space, excluding
the product itself.
"""
import csv
import os
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "products.csv")


@dataclass
class ProductRecord:
    name: str
    category: str
    brand: str
    price: float
    description: str
    embedding: Optional[np.ndarray] = field(default=None, repr=False)


class VectorStore:
    """Wraps a SentenceTransformer encoder + FAISS index over the product catalog."""

    def __init__(self, csv_path: str = DATA_PATH):
        # Imported lazily so importing this module (e.g. from recommender.py
        # for type references, or in tests) doesn't force a heavy
        # torch/sentence-transformers/faiss install unless a VectorStore is
        # actually instantiated.
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(_MODEL_NAME)
        self.products: List[ProductRecord] = self._load_products(csv_path)
        self.index, self.dim = self._build_index(self.products)

    def _load_products(self, csv_path: str) -> List[ProductRecord]:
        records = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(
                    ProductRecord(
                        name=row["name"],
                        category=row["category"],
                        brand=row["brand"],
                        price=float(row["price"]),
                        description=row["description"],
                    )
                )
        return records

    def _embed_text(self, p: ProductRecord) -> str:
        return f"{p.name}. Category: {p.category}. Brand: {p.brand}. {p.description}"

    def _build_index(self, products: List[ProductRecord]):
        import faiss

        texts = [self._embed_text(p) for p in products]
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        for p, vec in zip(products, embeddings):
            p.embedding = vec
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # inner product on normalized vecs = cosine similarity
        index.add(embeddings.astype("float32"))
        return index, dim

    def embed_query(self, text: str) -> np.ndarray:
        return self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True).astype("float32")

    def semantic_search(self, query: str, top_k: int = 8,
                         category: Optional[str] = None,
                         price_max: Optional[float] = None,
                         price_min: Optional[float] = None) -> List[dict]:
        query_vec = self.embed_query(query)
        # Over-fetch, then apply structured filters extracted by the NLU layer.
        scores, idxs = self.index.search(query_vec, min(len(self.products), top_k * 5))
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0:
                continue
            p = self.products[idx]
            if category and category.lower() not in p.category.lower() and category.lower() not in p.name.lower():
                continue
            if price_max is not None and p.price > price_max:
                continue
            if price_min is not None and p.price < price_min:
                continue
            results.append({
                "product": p.name, "category": p.category, "brand": p.brand,
                "price": p.price, "similarity": float(score),
            })
            if len(results) >= top_k:
                break
        return results

    def find_product(self, name: str) -> Optional[ProductRecord]:
        name_l = name.lower().strip()
        for p in self.products:
            if p.name.lower() == name_l:
                return p
        # fuzzy fallback: nearest neighbor by embedding
        query_vec = self.embed_query(name)
        scores, idxs = self.index.search(query_vec, 1)
        if idxs[0][0] >= 0 and scores[0][0] > 0.35:
            return self.products[idxs[0][0]]
        return None

    def substitutes(self, product_name: str, top_k: int = 3) -> List[dict]:
        target = self.find_product(product_name)
        if target is None:
            return []
        scores, idxs = self.index.search(
            target.embedding.reshape(1, -1).astype("float32"), top_k + 1
        )
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            p = self.products[idx]
            if p.name.lower() == target.name.lower():
                continue
            results.append({
                "product": p.name, "category": p.category,
                "price": p.price, "similarity": float(score),
            })
            if len(results) >= top_k:
                break
        return results

    def categorize(self, product_name: str) -> Optional[str]:
        """ML-based categorization: nearest catalog product's category, via embeddings
        rather than a hardcoded name->category lookup table."""
        p = self.find_product(product_name)
        return p.category if p else None


_store: Optional[VectorStore] = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
