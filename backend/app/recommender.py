"""
Hybrid recommendation engine.

Two real signals are combined, not a static/hardcoded suggestion list:

1. Collaborative-filtering-style signal: an item-item co-occurrence matrix
   built from `datasets/purchase_history.csv`. For a user's current
   cart/history, we look up which products most often appear in *other*
   users' baskets alongside those items ("customers who bought X also
   bought Y") - the classic market-basket approach behind collaborative
   filtering, without needing a full matrix-factorization model at this
   dataset size.

2. Content-based signal: sentence-transformer embeddings (via the shared
   VectorStore) give semantic similarity between what's in the user's
   history and the rest of the catalog - captures "milk -> other dairy"
   style relationships even for products that never co-occurred in the
   sample history.

Final score = weighted blend of both, and every recommendation carries a
human-readable reason describing *which* signal drove it (never a static
canned string irrespective of the actual math).
"""
import csv
import os
from collections import defaultdict
from typing import Dict, List, Optional

from .vector_store import VectorStore

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "purchase_history.csv")

COLLAB_WEIGHT = 0.6
CONTENT_WEIGHT = 0.4


class Recommender:
    def __init__(self, store: VectorStore, history_path: str = HISTORY_PATH):
        self.store = store
        self.baskets: Dict[str, List[str]] = self._load_baskets(history_path)
        self.co_occurrence = self._build_co_occurrence(self.baskets)

    def _load_baskets(self, path: str) -> Dict[str, List[str]]:
        baskets = defaultdict(list)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                baskets[row["user_id"]].append(row["product"])
        return baskets

    def _build_co_occurrence(self, baskets: Dict[str, List[str]]):
        co = defaultdict(lambda: defaultdict(int))
        for items in baskets.values():
            unique_items = list(set(items))
            for i, a in enumerate(unique_items):
                for b in unique_items[i + 1:]:
                    co[a][b] += 1
                    co[b][a] += 1
        return co

    def _collab_scores(self, seed_products: List[str]) -> Dict[str, float]:
        scores: Dict[str, float] = defaultdict(float)
        for item in seed_products:
            for other, count in self.co_occurrence.get(item, {}).items():
                if other in seed_products:
                    continue
                scores[other] += count
        if not scores:
            return {}
        max_score = max(scores.values())
        return {k: v / max_score for k, v in scores.items()}

    def _content_scores(self, seed_products: List[str], top_k: int = 20) -> Dict[str, float]:
        scores: Dict[str, float] = defaultdict(float)
        for item in seed_products:
            for sub in self.store.substitutes(item, top_k=top_k):
                if sub["product"] in seed_products:
                    continue
                scores[sub["product"]] = max(scores[sub["product"]], sub["similarity"])
        return scores

    def recommend(self, seed_products: List[str], top_k: int = 6) -> List[dict]:
        """seed_products = user's current shopping list + recent purchase history."""
        if not seed_products:
            # cold start: fall back to popular items across all sample baskets
            popularity = defaultdict(int)
            for items in self.baskets.values():
                for item in items:
                    popularity[item] += 1
            top = sorted(popularity.items(), key=lambda x: -x[1])[:top_k]
            results = []
            for name, count in top:
                p = self.store.find_product(name)
                results.append({
                    "product": name,
                    "category": p.category if p else None,
                    "price": p.price if p else None,
                    "score": count / max(popularity.values()),
                    "reason": "Popular starting point among other shoppers.",
                })
            return results

        collab = self._collab_scores(seed_products)
        content = self._content_scores(seed_products)

        all_candidates = set(collab) | set(content)
        blended = []
        for name in all_candidates:
            c_score = collab.get(name, 0.0)
            n_score = content.get(name, 0.0)
            final = COLLAB_WEIGHT * c_score + CONTENT_WEIGHT * n_score
            if c_score and n_score:
                reason = "Shoppers with similar purchase patterns bought this, and it's semantically similar to items in your list."
            elif c_score:
                reason = "Recommended because users with similar purchase patterns bought this item."
            else:
                reason = "Recommended because it's semantically similar to items already in your list."
            p = self.store.find_product(name)
            blended.append({
                "product": name,
                "category": p.category if p else None,
                "price": p.price if p else None,
                "score": round(final, 4),
                "reason": reason,
            })

        blended.sort(key=lambda x: -x["score"])
        return blended[:top_k]


_recommender: Optional[Recommender] = None


def get_recommender(store: VectorStore) -> Recommender:
    global _recommender
    if _recommender is None:
        _recommender = Recommender(store)
    return _recommender
