# Approach (200 words)

I built Sprout as a genuinely model-driven pipeline rather than a rule-based
chatbot. Voice is captured client-side with the Web Speech API and sent as
text to a FastAPI backend. There, intent classification runs through a
zero-shot NLI model (BART-MNLI) that scores the transcript against
natural-language hypotheses for each intent, so paraphrases like "I need
apples" and "add apples" resolve to the same intent through entailment, not
keyword matching. Entities (product, quantity, brand, price range) are
extracted with spaCy's statistical POS/NER tagging plus minimal regex for
numeric price parsing.

For search and substitution, I embed the product catalog with a
sentence-transformer and index it in FAISS, so "replace regular milk" or
"organic fruits below 300" are resolved by cosine similarity, not a lookup
table. Recommendations blend two real signals: an item-item co-occurrence
matrix built from sample purchase history (collaborative-filtering style)
and embedding similarity between the user's list and the catalog
(content-based) — each recommendation states which signal produced it.

Data lives in SQLite (Users, Products, ShoppingHistory, ShoppingList) to
keep the free-tier deployment simple. The React/Tailwind frontend shows the
live transcript, the AI's interpretation, the list, and recommendations,
with loading and error states throughout.
