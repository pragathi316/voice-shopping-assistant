from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class VoiceCommandRequest(BaseModel):
    text: str
    user_id: str = "guest"


class EntityResult(BaseModel):
    product: Optional[str] = None
    quantity: Optional[int] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price_max: Optional[float] = None
    price_min: Optional[float] = None


class VoiceCommandResponse(BaseModel):
    transcript: str
    intent: str
    intent_confidence: float
    entities: EntityResult
    action_result: Dict[str, Any]
    message: str


class AddItemRequest(BaseModel):
    user_id: str = "guest"
    product: str
    quantity: int = 1


class RemoveItemRequest(BaseModel):
    user_id: str = "guest"
    product: str


class UpdateItemRequest(BaseModel):
    user_id: str = "guest"
    product: str
    quantity: int


class ShoppingListItemOut(BaseModel):
    product: str
    quantity: int
    category: Optional[str] = None

    class Config:
        from_attributes = True


class RecommendationOut(BaseModel):
    product: str
    category: Optional[str] = None
    price: Optional[float] = None
    score: float
    reason: str


class SubstituteOut(BaseModel):
    product: str
    category: Optional[str] = None
    price: Optional[float] = None
    similarity: float
