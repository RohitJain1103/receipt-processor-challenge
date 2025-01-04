from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import List, Dict
import math

# Initialize FastAPI app
app = FastAPI(title="Receipt Processor", description="Receipt Processor", version="1.0.0")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "The receipt is invalid."}
    )

# In-memory storage for receipt IDs to their corresponding receipt json
receipt_storage: Dict[str, dict] = {}
# In-memory storage for mapping between receipt IDs and their points
receipt_points: Dict[str, int] = {}

class Item(BaseModel):
    shortDescription: str = Field(..., pattern=r"^[\w\s\-]+$")
    price: str = Field(..., pattern=r"^\d+\.\d{2}$")

class Receipt(BaseModel):
    retailer: str = Field(..., pattern=r"^[\w\s\-&]+$")
    purchaseDate: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    purchaseTime: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    items: List[Item]
    total: str = Field(..., pattern=r"^\d+\.\d{2}$")

# Utility functions
def calculate_points(receipt: Receipt) -> int:
    points = 0

    # Rule 1: One point for every alphanumeric character in the retailer name
    points += sum(char.isalnum() for char in receipt.retailer)

    # Rule 2: 50 points if the total is a round dollar amount with no cents
    if float(receipt.total).is_integer():
        points += 50

    # Rule 3: 25 points if the total is a multiple of 0.25
    if float(receipt.total) % 0.25 == 0:
        points += 25

    # Rule 4: 5 points for every two items on the receipt
    points += (len(receipt.items) // 2) * 5

    # Rule 5: Points for items with trimmed descriptions of length multiple of 3
    for item in receipt.items:
        description_length = len(item.shortDescription.strip())
        if description_length % 3 == 0:
            points += math.ceil(float(item.price) * 0.2)

    # Rule 6: 6 points if the day in the purchase date is odd
    day = int(receipt.purchaseDate.split("-")[2])
    if day % 2 != 0:
        points += 6

    # Rule 7: 10 points if the time of purchase is after 2:00 PM and before 4:00 PM
    hour, minute = map(int, receipt.purchaseTime.split(":"))
    if 14 <= hour < 16 and 0 < minute < 60:
        points += 10

    return points

# API Endpoints
@app.post("/receipts/process", response_model=dict)
def process_receipt(receipt: Receipt):
    receipt_id = str(uuid4())
    receipt_storage[receipt_id] = dict(receipt)
    receipt_points[receipt_id] = calculate_points(receipt)
    return {"id": receipt_id}

@app.get("/receipts/{id}/points", response_model=dict)
def get_receipt_points(id: str = Path(..., regex=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")):
    if id not in receipt_storage:
        raise HTTPException(status_code=404, detail="No receipt found for that ID.")
    return {"points": receipt_points[id]}
