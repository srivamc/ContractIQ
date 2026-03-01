from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import time

app = FastAPI(title=\"ContractIQ Demo App\", version=\"1.0.0\")

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

users_db = [
    {\"id\": 1, \"name\": \"Vamsee Srirama\", \"email\": \"vamsee@example.com\", \"age\": 35},
    {\"id\": 2, \"name\": \"Agent X\", \"email\": \"agentx@contractiq.ai\", \"age\": 2}
]

@app.get(\"/users\", response_model=List[User])
async def get_users():
    return users_db

@app.post(\"/users\", response_model=User)
async def create_user(user: User):
    if user.age < 0:
        raise HTTPException(status_code=400, detail=\"Age cannot be negative\")
    users_db.append(user.dict())
    return user

@app.get(\"/health\")
async def health_check():
    return {\"status\": \"healthy\", \"timestamp\": time.time()}

# Intentional vulnerability for GA-QE to find
@app.get(\"/admin/debug/logs\")
async def get_admin_logs(request: Request):
    # Missing authentication - GA-QE should flag this
    return {\"logs\": [\"User 1 logged in\", \"PII: SSN-XXX-XX-1234 accessed\"]}

if __name__ == \"__main__\":
    import uvicorn
    uvicorn.run(app, host=\"0.0.0.0\", port=8000)
