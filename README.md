# Sprout — Voice Command Shopping Assistant

A voice-driven shopping list manager with AI-powered intent understanding,
semantic search, product substitution, and hybrid recommendations.

Built for a Software Engineer technical assessment: real NLU and ML
techniques throughout — **no if/else intent trees, no keyword matching, no
hardcoded product responses.**

> See [`docs/WRITEUP.md`](docs/WRITEUP.md) for the 200-word approach summary
> and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full pipeline
> diagram and design rationale.

## Features

- **Voice input** — Web Speech API captures speech client-side; works with
  natural phrasing ("add apples" / "I need apples" / "please put apples in
  my cart" all resolve to the same intent).
- **Intent classification** — embedding-based few-shot classification: each
  of `ADD_ITEM`, `REMOVE_ITEM`, `UPDATE_ITEM`, `SEARCH_PRODUCT`,
  `SUBSTITUTE_PRODUCT`, `GET_RECOMMENDATION` is anchored by example
  phrasings, embedded with a sentence-transformer, and matched to the
  closest intent by cosine similarity — not entailment, not keywords.
- **Entity extraction** — spaCy statistical NER/POS for product, quantity,
  brand; regex only for parsing numeric price bounds ("under 200").
- **Semantic search** — sentence-transformer embeddings + FAISS vector
  index over the product catalog, with structured price/category filters
  layered on top of the similarity search.
- **AI product substitution** — nearest-neighbor lookup in embedding space;
  no manually stored substitute table.
- **Hybrid recommendation engine** — blends a collaborative-filtering-style
  item co-occurrence signal (built from sample purchase history) with
  content-based embedding similarity, and explains *why* each item was
  recommended.
- **Shopping list management** — add / remove / update quantity / view,
  with automatic category assignment via embedding similarity to the
  catalog (not a hardcoded name→category map).
- **Error handling** — empty voice input, unsupported browser / mic
  permission errors, API failures, and "not found" cases are all handled
  with user-facing messages.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | FastAPI (Python) |
| Speech-to-text | Web Speech API (browser-native, free) |
| Intent classification | `sentence-transformers` (`all-MiniLM-L6-v2`) few-shot exemplar matching |
| Entity extraction | spaCy (`en_core_web_sm`) |
| Semantic search / substitution | `sentence-transformers` (`all-MiniLM-L6-v2`) + FAISS |
| Recommendation engine | Custom hybrid: co-occurrence (collaborative) + embeddings (content-based) |
| Database | SQLite via SQLAlchemy (swap-compatible with MongoDB/Firebase — see Architecture doc) |
| Deployment | Frontend → Vercel; Backend → Render/Railway |

## Project structure
## Project structure

```
voice-shopping-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app + routes
│   │   ├── nlp.py             Intent classification + entity extraction
│   │   ├── vector_store.py    Embeddings + FAISS semantic search/substitution
│   │   ├── recommender.py     Hybrid recommendation engine
│   │   ├── database.py        SQLAlchemy models
│   │   └── schemas.py         Pydantic request/response models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/        VoiceButton, ShoppingList, Recommendations,
│   │   │                      SearchPanel, InterpretationPanel
│   │   ├── App.jsx
│   │   ├── api.js             API client
│   │   └── index.css
│   ├── package.json
│   └── .env.example
├── datasets/
│   ├── products.csv           50-item grocery catalog
│   └── purchase_history.csv   Sample multi-user basket data
├── docs/
│   ├── ARCHITECTURE.md
│   └── WRITEUP.md
└── README.md
```


## Local setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
uvicorn app.main:app --reload
```

First startup downloads the sentence-transformer model (MiniLM) — under
100MB, one-time. API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env       # set VITE_API_URL if backend isn't on localhost:8000
npm run dev
```

Open `http://localhost:5173`. Voice input requires Chrome/Edge (Web Speech
API support); other browsers can still use the text-command fallback field.

## API reference

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/voice/process` | Full pipeline: transcript → intent → entities → action → response |
| `POST` | `/api/shopping/add` | Add an item directly |
| `DELETE` | `/api/shopping/remove` | Remove an item |
| `PUT` | `/api/shopping/update` | Update item quantity |
| `GET` | `/api/shopping/list?user_id=` | Get the current list |
| `GET` | `/api/recommendations?user_id=` | Hybrid recommendations |
| `GET` | `/api/search?q=&price_max=&price_min=` | Semantic product search |
| `GET` | `/api/substitutes?product=` | Embedding-based substitutes |
| `GET` | `/api/health` | Health check |

Full interactive docs (OpenAPI/Swagger) are auto-generated by FastAPI at
`/docs` when the backend is running.

## Deployment

### Backend → Render (free tier)

1. Push this repo to GitHub.
2. On Render: **New → Web Service**, connect the repo, set root directory
   to `backend`.
3. Build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add env vars from `backend/.env.example`.
6. Note the deployed URL (e.g. `https://sprout-api.onrender.com`).

*(Railway or AWS work the same way — see `backend/Dockerfile` for a
container-based alternative.)*

### Frontend → Vercel

1. Import the repo on Vercel, set root directory to `frontend`.
2. Build command: `npm run build` — output directory: `dist`.
3. Add env var `VITE_API_URL` = your deployed backend URL.
4. Deploy.

## Testing

Run the backend's syntax/import checks and add unit tests for the NLU,
recommender, and API layers under `backend/tests/` (see
`backend/tests/test_recommender.py` for the seeded example covering the
co-occurrence and blended scoring logic). Extend with `pytest` for the
`/api/*` endpoints using FastAPI's `TestClient`.

## Future improvements

- Multilingual voice input (Whisper multilingual model instead of/alongside
  Web Speech API, for non-English commands).
- Replace the synthetic purchase-history CSV with the real Instacart
  Market Basket dataset for a richer collaborative signal.
- Matrix-factorization or a learned ranking model once enough real
  interaction data exists, instead of raw co-occurrence counts.
- Auth + persistent user accounts (currently a single `guest` user_id by
  default, though the API already supports arbitrary `user_id`s).
- Seasonal/sale-aware recommendations by joining in a promotions feed.

## Deliverables checklist

- [x] Working application (run locally per instructions above; deploy per
      the steps above for a hosted URL)
- [x] GitHub-ready repository with source code and this README
- [x] 200-word approach write-up (`docs/WRITEUP.md`)