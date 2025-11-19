import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from schemas import ContactMessage, TrackEvent, CheckoutRequest

app = FastAPI(title="Ascendia API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Ascendia API running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the Ascendia backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# -----------------------------
# Contact form endpoint
# -----------------------------
@app.post("/api/contact")
def submit_contact(payload: ContactMessage):
    try:
        from database import create_document
        doc_id = create_document("contactmessage", payload)
        return {"status": "ok", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

# -----------------------------
# Analytics tracking endpoint
# -----------------------------
@app.post("/api/track")
def track_event(payload: TrackEvent):
    try:
        from database import create_document
        if payload.timestamp is None:
            payload.timestamp = datetime.utcnow()
        doc_id = create_document("trackevent", payload)
        return {"status": "ok", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track event: {str(e)}")

# -----------------------------
# Stripe Checkout endpoint
# -----------------------------
class CheckoutResponse(BaseModel):
    url: str

@app.post("/api/create-checkout-session", response_model=CheckoutResponse)
def create_checkout_session(payload: CheckoutRequest):
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        raise HTTPException(status_code=400, detail="Stripe is not configured. Set STRIPE_SECRET_KEY environment variable.")

    try:
        import stripe
        stripe.api_key = secret_key

        success_url = payload.success_url or os.getenv("FRONTEND_URL", "http://localhost:3000") + "/?success=true"
        cancel_url = payload.cancel_url or os.getenv("FRONTEND_URL", "http://localhost:3000") + "/?canceled=true"

        if payload.price_id:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{"price": payload.price_id, "quantity": payload.quantity or 1}],
                success_url=success_url,
                cancel_url=cancel_url,
            )
        else:
            if not payload.amount or not payload.name:
                raise HTTPException(status_code=422, detail="Provide amount (in cents) and name when not using price_id")
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": payload.currency or "usd",
                        "product_data": {"name": payload.name, "description": payload.description or "Ascendia Course"},
                        "unit_amount": payload.amount,
                    },
                    "quantity": payload.quantity or 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
            )
        return {"url": session.url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
