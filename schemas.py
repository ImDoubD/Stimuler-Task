from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr

class ConversationCreate(BaseModel):
    user_id: UUID

class UtteranceCreate(BaseModel):
    conversation_id: UUID
    user_id: UUID
    content: Optional[str] = None
    
class ErrorModel(BaseModel):
    errorCategory: str
    errorSubCategory: str

class InputData(BaseModel):
    user_id: UUID
    conversation_id: UUID
    utterance_id: UUID
    errors: List[ErrorModel]