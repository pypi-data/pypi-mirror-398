from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from lazy_crawler.app.database import get_session, User, DatasetMetadata
from lazy_crawler.app import config
from lazy_crawler.app.auth import get_current_user
from sqlmodel.ext.asyncio.session import AsyncSession
from pymongo import MongoClient
import pandas as pd
import uuid
import os
import io

from sqlmodel import select
from typing import List

router = APIRouter(prefix="/datasets", tags=["datasets"])

# MongoDB Connection
client = MongoClient(config.MONGO_URI)
db = client[config.MONGO_DATABASE]


@router.get("/list", response_model=List[DatasetMetadata])
async def list_user_datasets(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all datasets uploaded by the current user.
    """
    statement = select(DatasetMetadata).where(
        DatasetMetadata.user_id == current_user.id
    )
    result = await session.execute(statement)
    datasets = result.scalars().all()
    return datasets


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # 1. Validation
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400, detail="Only CSV and Excel files are allowed."
        )

    # 2. Read File Content
    content = await file.read()
    file_size = len(content)

    datasets_to_process = []  # List of (df, display_name)

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
            datasets_to_process.append((df, filename))
        else:
            # For Excel, read all sheets
            excel_data = pd.read_excel(io.BytesIO(content), sheet_name=None)
            for sheet_name, df in excel_data.items():
                display_name = f"{filename} [{sheet_name}]"
                datasets_to_process.append((df, display_name))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    if not datasets_to_process:
        raise HTTPException(
            status_code=400, detail="File is empty or could not be parsed."
        )

    responses = []

    for df, display_name in datasets_to_process:
        # 3. Generate Sync ID and Prepare Mongo Data
        sync_id = str(uuid.uuid4())
        collection_name = f"dataset_{sync_id}"

        # Convert DataFrame to list of dicts for Mongo
        # fillna to avoid NaN in Mongo
        records = df.fillna("").to_dict(orient="records")

        if not records:
            continue  # Skip empty sheets

        # 4. Save to MongoDB
        try:
            collection = db[collection_name]
            collection.insert_many(records)
        except Exception as e:
            # We might want to rollback but for now let's just log or raise
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save {display_name} to MongoDB: {str(e)}",
            )

        # 5. Save Metadata to PostgreSQL
        new_dataset = DatasetMetadata(
            sync_id=sync_id,
            filename=display_name,
            file_type=ext,
            file_size=file_size,  # This is the total file size
            mongo_collection_name=collection_name,
            user_id=current_user.id,
        )

        session.add(new_dataset)
        responses.append(
            {
                "sync_id": sync_id,
                "collection_name": collection_name,
                "filename": display_name,
                "record_count": len(records),
            }
        )

    await session.commit()

    return {
        "message": f"Dataset uploaded successfully ({len(responses)} sheets/files processed)",
        "datasets": responses,
        "collection_name": responses[0]["collection_name"]
        if responses
        else None,  # For UI backwards compatibility
    }
