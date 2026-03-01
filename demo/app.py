import os, hashlib, time, random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# --- ContractIQ Feature Flag Loader ---
# Reads config.yaml or environment variables to toggle features
class FeatureFlags:
    AGENT_SWARM_ENABLED       = os.getenv("CIQ_AGENT_SWARM", "true") == "true"
    ADVERSARIAL_QE_ENABLED    = os.getenv("CIQ_ADVERSARIAL_QE", "true") == "true"
    IMMUTABLE_LEDGER_ENABLED  = os.getenv("CIQ_IMMUTABLE_LEDGER", "false") == "true"
    ZK_PROOFS_ENABLED         = os.getenv("CIQ_ZK_PROOFS", "true") == "true"
    COMPLIANCE_ACaC_ENABLED   = os.getenv("CIQ_COMPLIANCE_ACaC", "true") == "true"
    SYNTHETIC_DATA_ENABLED    = os.getenv("CIQ_SYNTHETIC_DATA", "true") == "true"

app = FastAPI(title="ContractIQ Synthetic Demo App", version="2.0.0")

# --- Models ---
class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

class Order(BaseModel):
    order_id: str
    user_id: int
    amount: float
    status: str

class QualityProof(BaseModel):
    contract: str
    result: str
    zk_hash: Optional[str] = None
    ledger_tx: Optional[str] = None

# --- Synthetic Database ---
users_db = [
    {"id": 1, "name": "Vamsee Srirama", "email": "vamsee@example.com", "age": 35},
    {"id": 2, "name": "Agent X", "email": "agentx@contractiq.ai", "age": 2}
]
orders_db = []
ledger = []  # In-memory blockchain ledger (activated by flag)

# --- Feature-Gated Helpers ---
def compute_zk_proof(payload: dict) -> str:
    """Compute ZK-style hash of a contract result (stubbed for demo)."""
    raw = str(sorted(payload.items()))
    return "zk:" + hashlib.sha256(raw.encode()).hexdigest()[:32]

def record_to_ledger(proof_hash: str) -> str:
    """Append to immutable in-memory ledger if IMMUTABLE_LEDGER flag is ON."""
    if FeatureFlags.IMMUTABLE_LEDGER_ENABLED:
        tx_id = f"TX-{len(ledger)+1:04d}-{hashlib.md5(proof_hash.encode()).hexdigest()[:8]}"
        ledger.append({"tx_id": tx_id, "hash": proof_hash, "ts": time.time()})
        return tx_id
    return None

# --- API Endpoints ---

@app.get("/users", response_model=List[User])
async def get_users():
    return users_db

@app.post("/users", response_model=User)
async def create_user(user: User):
    users_db.append(user.dict())
    return user

@app.get("/orders/{user_id}", response_model=List[Order])
async def get_orders(user_id: int):
    return [o for o in orders_db if o["user_id"] == user_id]

@app.post("/orders", response_model=Order)
async def create_order(order: Order):
    time.sleep(0.1)
    orders_db.append(order.dict())
    return order

@app.get("/config")
async def get_config():
    """Returns active feature flags so the agentic framework can discover capabilities."""
    return {
        "version": "2.0.0",
        "feature_flags": {
            "agent_swarm": FeatureFlags.AGENT_SWARM_ENABLED,
            "adversarial_qe": FeatureFlags.ADVERSARIAL_QE_ENABLED,
            "immutable_ledger": FeatureFlags.IMMUTABLE_LEDGER_ENABLED,
            "zk_proofs": FeatureFlags.ZK_PROOFS_ENABLED,
            "compliance_acac": FeatureFlags.COMPLIANCE_ACaC_ENABLED,
            "synthetic_data": FeatureFlags.SYNTHETIC_DATA_ENABLED,
        }
    }

@app.get("/quality-proof", response_model=QualityProof)
async def run_quality_proof(contract: str = "POST /users"):
    """Demonstrates ZK-QP + optional Blockchain Ledger recording."""
    result_payload = {"contract": contract, "status": "PASS", "ts": time.time()}
    proof = QualityProof(contract=contract, result="PASS")

    if FeatureFlags.ZK_PROOFS_ENABLED:
        proof.zk_hash = compute_zk_proof(result_payload)

    if FeatureFlags.IMMUTABLE_LEDGER_ENABLED and proof.zk_hash:
        proof.ledger_tx = record_to_ledger(proof.zk_hash)

    return proof

@app.get("/ledger")
async def get_ledger():
    """Returns the immutable quality ledger (only active if flag is ON)."""
    if not FeatureFlags.IMMUTABLE_LEDGER_ENABLED:
        return {"status": "disabled", "message": "Set CIQ_IMMUTABLE_LEDGER=true to activate blockchain ledger."}
    return {"entries": ledger}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
