from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from uuid import UUID
from models import Error, ErrorFrequency, User, Utterance, Conversation, Base
from database import get_db
import json
from schemas import UserCreate, ConversationCreate, UtteranceCreate, ErrorModel, InputData
from utils import update_error_frequencies, process_batch_update

app = FastAPI()


# POST API for creating a User
@app.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# POST API for creating a Conversation for a User
@app.post("/conversations/", response_model=ConversationCreate)
def create_conversation(conversation: ConversationCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_id == conversation.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_conversation = Conversation(user_id=conversation.user_id)
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation

# POST API for creating an Utterance in a User's Conversation
@app.post("/utterances/", response_model=UtteranceCreate)
def create_utterance(utterance: UtteranceCreate, db: Session = Depends(get_db)):
    db_conversation = db.query(Conversation).filter(Conversation.conversation_id == utterance.conversation_id).first()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    new_utterance = Utterance(conversation_id=utterance.conversation_id, user_id=utterance.user_id, content=utterance.content)
    db.add(new_utterance)
    db.commit()
    db.refresh(new_utterance)
    return new_utterance

# to test and simulate the error frequency working
@app.post("/simulate-and-generate")
def simulate_and_generate(input_data: InputData, db: Session = Depends(get_db)):
    user_id = input_data.user_id
    conversation_id = input_data.conversation_id
    utterance_id = input_data.utterance_id
    errors = input_data.errors

    # Frequency Updation
    update_error_frequencies(user_id, conversation_id, utterance_id, errors, db)
    # Batch processing
    process_batch_update(db)

    return {"message": "Error frequencies simulated and batch processing triggered successfully."}

@app.get("/generate-exercise")
def generate_exercise(user_id: UUID, top_n: int = 5, db: Session = Depends(get_db)):
    errors = db.query(ErrorFrequency).filter(
        ErrorFrequency.user_id == user_id
    ).order_by(desc(ErrorFrequency.frequency)).limit(top_n).all()
    
    if not errors:
        raise HTTPException(status_code=404, detail="No errors found for the given user")

    top_errors = [
        {
            "errorCategory": error.error_category,
            "errorSubCategory": error.error_subcategory,
            "errorFrequency": error.frequency
        }
        for error in errors
    ]

    return {"top_errors": top_errors}



