# Architecture

## Pipeline

```
 Browser mic
     │  Web Speech API (speech-to-text, runs client-side)
     ▼
 Transcript (text)
     │  POST /api/voice/process
     ▼
 ┌─────────────────────────────────────────────┐
 │  NLU (backend/app/nlp.py)                    │
 │  1. Intent classification                    │
 │     zero-shot pipeline (facebook/bart-large  │
 │     -mnli): compares the transcript against  │
 │     natural-language hypotheses for each      │
 │     intent via entailment — not keywords.     │
 │  2. Entity extraction                         │
 │     spaCy statistical NER/POS for product     │
 │     noun phrases + quantities; light regex    │
 │     only for parsing numeric price bounds.    │
 └─────────────────────────────────────────────┘
     │  intent + entities
     ▼
 ┌─────────────────────────────────────────────┐
 │  Shopping Action (backend/app/main.py)        │
 │  ADD_ITEM / REMOVE_ITEM / UPDATE_ITEM /       │
 │  SEARCH_PRODUCT / SUBSTITUTE_PRODUCT /        │
 │  GET_RECOMMENDATION                           │
 └─────────────────────────────────────────────┘
     │
     ├──▶ Vector Store (backend/app/vector_store.py)
     │     sentence-transformers (all-MiniLM-L6-v2) embeddings
     │     + FAISS IndexFlatIP (cosine similarity) over the
     │     product catalog → semantic search, substitution,
     │     and embedding-based auto-categorization.
     │
     └──▶ Recommender (backend/app/recommender.py)
           Hybrid score = 0.6 × collaborative signal
                         + 0.4 × content signal
           - Collaborative: item-item co-occurrence built from
             datasets/purchase_history.csv (market-basket style).
           - Content: cosine similarity between the user's
             history/list and the rest of the catalog.
     │
     ▼
 Response Generation
     │  JSON: transcript, intent, confidence, entities,
     │  action_result, human-readable message
     ▼
 React UI renders transcript, AI interpretation, updated list,
 and recommendations.
```

## Why these choices

- **No hardcoded intent rules.** Intents are matched by comparing the
  transcript to natural-language hypotheses through an NLI model's
  entailment score, so paraphrases ("I need apples" / "please put apples
  in my cart" / "add apples") land on the same intent without any
  if/else or keyword table.
- **No hardcoded substitute tables.** "Replace regular milk" works by
  embedding "milk" and doing a FAISS nearest-neighbor search over the
  catalog — almond/soy/oat milk surface because they're semantically
  close, not because they were manually linked to "milk".
- **Recommendations are computed, not static.** The co-occurrence matrix
  and embedding similarities are recalculated from the underlying data;
  swapping in a larger purchase-history dataset changes the
  recommendations without touching any code.
- **SQLite instead of MongoDB/Firebase.** Functionally equivalent
  document/collection shape (Users, Products, ShoppingHistory,
  ShoppingList), but zero external service to provision — keeps the
  free-tier deployment simple. Swapping to MongoDB later only touches
  `database.py`.

## Data model

| Collection/Table  | Fields |
|---|---|
| `users` | `user_id`, `preferences` (JSON) |
| `products` | `name`, `category`, `brand`, `price`, `description`, `embedding` |
| `shopping_history` | `user_id`, `product`, `timestamp` |
| `shopping_list` | `user_id`, `product`, `quantity`, `category` |

## Dataset

`datasets/products.csv` — a 50-item grocery catalog spanning dairy,
produce, snacks, grains, beverages, household, and personal care,
each with a short description used to build embeddings.

`datasets/purchase_history.csv` — synthetic multi-user basket data
(15 users, 3–4 items per basket) modeled on the shape of the Instacart
Market Basket dataset, used to seed the collaborative-filtering signal.
Both are small on purpose for an 8-hour build; the loading code in
`vector_store.py` and `recommender.py` doesn't care about scale, so
either file can be swapped for the real Instacart or Amazon product
datasets without changing any application logic.
