
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .schemas import FinalBrief
from .workflow import build_and_run

app = FastAPI(title="Context-Aware Research Brief API (HF, no OpenAI)")

class BriefRequest(BaseModel):
    topic: str
    depth: int = 1
    follow_up: bool = False
    user_id: str

@app.post("/brief", response_model=FinalBrief)
def brief(req: BriefRequest):
    if len(req.topic.strip()) < 3:
        raise HTTPException(status_code=400, detail="Topic too short")
    final = build_and_run(topic=req.topic, depth=req.depth, user_id=req.user_id, follow_up=req.follow_up)
    try:
        return FinalBrief(**final)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Output validation failed: {e}")
