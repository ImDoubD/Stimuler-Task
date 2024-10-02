from collections import defaultdict
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from models import Error, ErrorFrequency, User, Utterance, Conversation, Base
from database import get_db
import json
from redis import Redis
from schemas import ErrorModel


redis_cache = Redis(host='localhost', port=6379, decode_responses=True)

BATCH_INTERVAL = 10 * 60  # 10 minutes

def update_error_frequencies(user_id: UUID, conversation_id: UUID, utterance_id: UUID, errors: List[ErrorModel], db: Session):
    error_frequencies = defaultdict(int)

    for error in errors:
        error_category = error.errorCategory  # Accessing Pydantic model attributes with dot notation
        error_subcategory = error.errorSubCategory
        key = f"{user_id}:{error_category}:{error_subcategory}"

        cache_value = redis_cache.get(key)

        if cache_value is None:
            db_entry = db.query(ErrorFrequency).filter(
                ErrorFrequency.user_id == user_id,
                ErrorFrequency.error_category == error_category,
                ErrorFrequency.error_subcategory == error_subcategory
            ).first()
            if db_entry:
                # Populate the cache with the value from the database
                redis_cache.set(key, db_entry.frequency)
                cache_value = db_entry.frequency
            else:
                # If neither cache nor DB contains this, start from zero
                cache_value = 0

        # Increment the cache value
        new_value = int(cache_value) + 1
        redis_cache.set(key, new_value)

        # Collect frequencies for batch processing
        error_frequencies[(error_category, error_subcategory)] += 1

    # Call queue_batch_update to queue the batch job in Redis
    queue_batch_update(user_id, error_frequencies, db)

    return error_frequencies


def queue_batch_update(user_id: UUID, error_frequencies: defaultdict, db: Session):
    """
    Queue the frequencies in Redis and schedule a batch process to update the database.
    The batch job will process unique (error_category, error_subcategory) combinations
    and update the database in one go.
    """
    for (error_category, error_subcategory), count in error_frequencies.items():
        batch_key = f"batch:{user_id}:{error_category}:{error_subcategory}"

        try:
            # Increment the frequency in Redis batch queue
            redis_cache.incrby(batch_key, count)

            # Set expiration only if it's a new batch key
            if not redis_cache.exists(batch_key):
                redis_cache.expire(batch_key, BATCH_INTERVAL)

        except redis_cache.RedisError as e:
            # Handle Redis failure (e.g., logging, fallback)
            print(f"Redis error while processing {batch_key}: {e}")

def process_batch_update(db: Session):
    """
    This function runs periodically to process the batch data from Redis and update the database.
    It reads the batch data from Redis, aggregates it, and updates the database in one go.
    """
    for batch_key in redis_cache.scan_iter("batch:*"):
        # Extract user_id, error_category, error_subcategory from the key
        _, user_id, error_category, error_subcategory = batch_key.split(":")
        user_id = UUID(user_id)

        try:
            # Get the accumulated frequency count
            frequency = int(redis_cache.get(batch_key))

            # Check if the record exists in the database
            db_entry = db.query(ErrorFrequency).filter(
                ErrorFrequency.user_id == user_id,
                ErrorFrequency.error_category == error_category,
                ErrorFrequency.error_subcategory == error_subcategory
            ).first()

            if db_entry:
                # If entry exists, update the frequency
                db_entry.frequency += frequency
            else:
                # If entry doesn't exist, create a new one
                db_entry = ErrorFrequency(
                    user_id=user_id,
                    error_category=error_category,
                    error_subcategory=error_subcategory,
                    frequency=frequency
                )
                db.add(db_entry)

            # Commit the changes to the database
            db.commit()

            # Remove the key from Redis after processing
            redis_cache.delete(batch_key)

        except redis_cache.RedisError as e:
            print(f"Redis error during batch processing for {batch_key}: {e}")
        except Exception as e:
            print(f"Error during batch processing for {batch_key}: {e}")