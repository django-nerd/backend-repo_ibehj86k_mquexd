"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Ascendia app schemas

class ContactMessage(BaseModel):
    """
    Contact messages from the landing page
    Collection name: "contactmessage"
    """
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=5000)
    source: Optional[str] = Field(None, description="Where the message came from (page/section)")

class TrackEvent(BaseModel):
    """
    Analytics events from the landing page
    Collection name: "trackevent"
    """
    event: str = Field(..., description="Event name, e.g., page_view, cta_click")
    path: Optional[str] = Field(None, description="Page path")
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None

class CheckoutRequest(BaseModel):
    """
    Request to create a Stripe Checkout Session
    Not persisted; used for validation
    """
    price_id: Optional[str] = Field(None, description="Stripe Price ID if using recurring or predefined prices")
    name: Optional[str] = Field(None, description="Name of the course/product if using ad-hoc price")
    description: Optional[str] = None
    amount: Optional[int] = Field(None, ge=50, description="Amount in cents when not using price_id")
    currency: str = Field("usd", description="Currency code")
    quantity: int = Field(1, ge=1)
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
