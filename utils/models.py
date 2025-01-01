from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class LineItem(BaseModel):
    description: str
    quantity: Optional[float]
    unit_price: Optional[float]
    total: Optional[float]


class ReceiptData(BaseModel):
    merchant_name: str
    date: Optional[datetime]
    total_amount: float
    currency: str
    items: List[LineItem]
    tax_amount: Optional[float]
    payment_method: Optional[str]
    receipt_number: Optional[str]
    detected_text: str
