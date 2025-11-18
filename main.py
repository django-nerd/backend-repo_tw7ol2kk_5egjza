import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict

from database import db, create_document, get_documents
from schemas import ContactMessage, Pledge

app = FastAPI(title="SAM Foundation Charity Trust API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "SAM Foundation Charity Trust API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Welcome to SAM Foundation Charity Trust"}

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
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# Public schemas endpoint for tooling
@app.get("/schema")
def get_schema() -> Dict[str, Any]:
    return {
        "collections": {
            "contactmessage": ContactMessage.model_json_schema(),
            "pledge": Pledge.model_json_schema(),
        }
    }

# Contact message submission
@app.post("/api/contact")
def submit_contact(message: ContactMessage):
    try:
        inserted_id = create_document("contactmessage", message)
        return {"status": "success", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Donation pledge submission
@app.post("/api/pledge")
def submit_pledge(pledge: Pledge):
    try:
        inserted_id = create_document("pledge", pledge)
        return {"status": "success", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Recent pledges (limited)
@app.get("/api/pledges")
def list_pledges(limit: int = 10):
    try:
        docs = get_documents("pledge", limit=limit)
        # Convert ObjectId and datetime fields to strings for JSON
        def normalize(doc):
            doc = dict(doc)
            if "_id" in doc:
                doc["id"] = str(doc.pop("_id"))
            for k, v in list(doc.items()):
                if hasattr(v, "isoformat"):
                    doc[k] = v.isoformat()
            return doc
        return [normalize(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
