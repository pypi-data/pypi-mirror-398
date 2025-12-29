"""
Data routes - MongoDB collections and data endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from lazy_crawler.app import config
from pymongo import MongoClient
from typing import Optional

router = APIRouter(tags=["data"])

# MongoDB Connection
client = MongoClient(config.MONGO_URI)
db = client[config.MONGO_DATABASE]


@router.get("/collections")
def list_collections():
    """
    List all available scraped datasets (collections).
    """
    collections = db.list_collection_names()
    return {"collections": collections}


@router.get("/data/{collection_name}")
def get_data(
    collection_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
):
    """
    Retrieve items from a specific collection with pagination and basic search.

    Args:
        collection_name: Name of the MongoDB collection
        page: Page number (default 1)
        page_size: Items per page (default 20, max 100)
        q: Optional search query

    Returns:
        Items from collection with pagination metadata
    """
    if collection_name not in db.list_collection_names():
        raise HTTPException(status_code=404, detail="Collection not found")

    collection = db[collection_name]

    # Basic search filter if 'q' is provided (search in all string fields)
    filter_query = {}
    if q:
        filter_query = {"$or": [{"$text": {"$search": q}}]}
        # Note: Text index must be created in MongoDB for this to work perfectly.
        # Fallback for simple regex if index is not present:
        # filter_query = {"$or": [{"title": {"$regex": q, "$options": "i"}}, {"description": {"$regex": q, "$options": "i"}}]}

    skip = (page - 1) * page_size
    items = list(collection.find(filter_query).skip(skip).limit(page_size))

    # Convert MongoDB _id to string
    for item in items:
        if "_id" in item:
            item["_id"] = str(item["_id"])

    total_count = collection.count_documents(filter_query)

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_items": total_count,
        "total_pages": (total_count + page_size - 1) // page_size,
    }
