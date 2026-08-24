from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import schemas, nlp
from .database import init_db, get_db, User, ShoppingListItem, ShoppingHistory
from .vector_store import get_store
from .recommender import get_recommender

app = FastAPI(
    title="Voice Command Shopping Assistant API",
    description="AI-driven voice shopping assistant: NLU intent/entity extraction, "
                 "semantic search & substitution, and a hybrid recommender.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    # Warm the ML models once at startup so the first request isn't slow.
    get_store()


def _get_or_create_user(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, preferences={})
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _add_item(db: Session, user_id: str, product: str, quantity: int) -> dict:
    _get_or_create_user(db, user_id)
    store = get_store()
    category = store.categorize(product)

    existing = (
        db.query(ShoppingListItem)
        .filter(ShoppingListItem.user_id == user_id, ShoppingListItem.product.ilike(product))
        .first()
    )
    if existing:
        existing.quantity += quantity
    else:
        db.add(ShoppingListItem(user_id=user_id, product=product, quantity=quantity, category=category))

    db.add(ShoppingHistory(user_id=user_id, product=product))
    db.commit()
    return {"product": product, "quantity": quantity, "category": category, "status": "added"}


def _remove_item(db: Session, user_id: str, product: str) -> dict:
    item = (
        db.query(ShoppingListItem)
        .filter(ShoppingListItem.user_id == user_id, ShoppingListItem.product.ilike(product))
        .first()
    )
    if not item:
        return {"product": product, "status": "not_found"}
    db.delete(item)
    db.commit()
    return {"product": product, "status": "removed"}


def _update_item(db: Session, user_id: str, product: str, quantity: int) -> dict:
    item = (
        db.query(ShoppingListItem)
        .filter(ShoppingListItem.user_id == user_id, ShoppingListItem.product.ilike(product))
        .first()
    )
    if not item:
        return {"product": product, "status": "not_found"}
    item.quantity = quantity
    db.commit()
    return {"product": product, "quantity": quantity, "status": "updated"}


@app.post("/api/voice/process", response_model=schemas.VoiceCommandResponse)
def process_voice_command(req: schemas.VoiceCommandRequest, db: Session = Depends(get_db)):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty voice input. Please try speaking again.")

    try:
        result = nlp.analyze(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLU processing failed: {e}")

    entities = schemas.EntityResult(
        product=result.product, quantity=result.quantity, brand=result.brand,
        category=result.category, price_max=result.price_max, price_min=result.price_min,
    )

    action_result: dict = {}
    message = ""
    store = get_store()

    if result.intent == "ADD_ITEM":
        product = result.product or req.text
        qty = result.quantity or 1
        action_result = _add_item(db, req.user_id, product, qty)
        message = f"Added {qty} x {product} to your shopping list."

    elif result.intent == "REMOVE_ITEM":
        product = result.product or req.text
        action_result = _remove_item(db, req.user_id, product)
        message = (f"Removed {product} from your list."
                    if action_result["status"] == "removed"
                    else f"Couldn't find {product} on your list.")

    elif result.intent == "UPDATE_ITEM":
        product = result.product or req.text
        qty = result.quantity or 1
        action_result = _update_item(db, req.user_id, product, qty)
        message = (f"Updated {product} to quantity {qty}."
                    if action_result["status"] == "updated"
                    else f"Couldn't find {product} on your list to update.")

    elif result.intent == "SEARCH_PRODUCT":
        query = result.category or result.product or req.text
        matches = store.semantic_search(
            query, top_k=6, price_max=result.price_max, price_min=result.price_min,
        )
        action_result = {"results": matches}
        message = f"Found {len(matches)} product(s) matching '{query}'."

    elif result.intent == "SUBSTITUTE_PRODUCT":
        product = result.product or req.text
        subs = store.substitutes(product, top_k=4)
        action_result = {"substitutes": subs}
        message = (f"Here are some alternatives to {product}." if subs
                    else f"Couldn't find alternatives for {product}.")

    elif result.intent == "GET_RECOMMENDATION":
        history_products = [
            h.product for h in
            db.query(ShoppingHistory).filter(ShoppingHistory.user_id == req.user_id).all()
        ]
        recommender = get_recommender(store)
        recs = recommender.recommend(list(dict.fromkeys(history_products)), top_k=6)
        action_result = {"recommendations": recs}
        message = f"Here are {len(recs)} recommendation(s) based on your shopping activity."

    else:
        message = "Sorry, I didn't understand that command."

    return schemas.VoiceCommandResponse(
        transcript=req.text,
        intent=result.intent,
        intent_confidence=round(result.confidence, 4),
        entities=entities,
        action_result=action_result,
        message=message,
    )


@app.post("/api/shopping/add")
def add_item(req: schemas.AddItemRequest, db: Session = Depends(get_db)):
    return _add_item(db, req.user_id, req.product, req.quantity)


@app.delete("/api/shopping/remove")
def remove_item(req: schemas.RemoveItemRequest, db: Session = Depends(get_db)):
    result = _remove_item(db, req.user_id, req.product)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=f"{req.product} not found on shopping list.")
    return result


@app.put("/api/shopping/update")
def update_item(req: schemas.UpdateItemRequest, db: Session = Depends(get_db)):
    result = _update_item(db, req.user_id, req.product, req.quantity)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=f"{req.product} not found on shopping list.")
    return result


@app.get("/api/shopping/list", response_model=list[schemas.ShoppingListItemOut])
def get_list(user_id: str = "guest", db: Session = Depends(get_db)):
    return db.query(ShoppingListItem).filter(ShoppingListItem.user_id == user_id).all()


@app.get("/api/recommendations", response_model=list[schemas.RecommendationOut])
def get_recommendations(user_id: str = "guest", db: Session = Depends(get_db)):
    store = get_store()
    history_products = [
        h.product for h in
        db.query(ShoppingHistory).filter(ShoppingHistory.user_id == user_id).all()
    ]
    list_products = [
        i.product for i in
        db.query(ShoppingListItem).filter(ShoppingListItem.user_id == user_id).all()
    ]
    seed = list(dict.fromkeys(list_products + history_products))
    recommender = get_recommender(store)
    return recommender.recommend(seed, top_k=6)


@app.get("/api/search")
def search(q: str, price_max: Optional[float] = None, price_min: Optional[float] = None):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    store = get_store()
    return {"results": store.semantic_search(q, top_k=8, price_max=price_max, price_min=price_min)}


@app.get("/api/substitutes")
def get_substitutes(product: str):
    store = get_store()
    subs = store.substitutes(product, top_k=4)
    if not subs:
        raise HTTPException(status_code=404, detail=f"No substitutes found for '{product}'.")
    return {"product": product, "substitutes": subs}


@app.get("/api/health")
def health():
    return {"status": "ok"}
