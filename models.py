from sqlalchemy import Column, ForeignKey, String, Text, TIMESTAMP, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

# User table model
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")
    utterances = relationship("Utterance", back_populates="user")
    errors = relationship("Error", back_populates="user")
    error_frequencies = relationship("ErrorFrequency", back_populates="user")


# Conversation table model
class Conversation(Base):
    __tablename__ = "conversations"
    
    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    started_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    utterances = relationship("Utterance", back_populates="conversation")
    errors = relationship("Error", back_populates="conversation")


# Utterance table model
class Utterance(Base):
    __tablename__ = "utterances"
    
    utterance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.conversation_id', ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="utterances")
    user = relationship("User", back_populates="utterances")


# Error table model
class Error(Base):
    __tablename__ = "errors"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False, primary_key=True)
    error_category = Column(Text, nullable=False, primary_key=True)
    error_subcategory = Column(Text, nullable=False, primary_key=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.conversation_id', ondelete="CASCADE"), nullable=False, primary_key=True)
    utterance_id = Column(UUID(as_uuid=True), ForeignKey('utterances.utterance_id', ondelete="CASCADE"), nullable=False, primary_key=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow, primary_key=True)

    user = relationship("User", back_populates="errors")
    conversation = relationship("Conversation", back_populates="errors")


# ErrorFrequency table model
class ErrorFrequency(Base):
    __tablename__ = "error_frequencies"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False, primary_key=True)
    error_category = Column(Text, nullable=False, primary_key=True)
    error_subcategory = Column(Text, nullable=False, primary_key=True)
    frequency = Column(BigInteger, default=0)

    user = relationship("User", back_populates="error_frequencies")
