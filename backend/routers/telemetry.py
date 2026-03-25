from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from auth import get_current_user
from rabbitmq_client import publish_event

router = APIRouter()

class ClickEvent(BaseModel):
    user_id: str
    url: str
    page_context: str
    timestamp: datetime

@router.post("/api/v1/telemetry/click", status_code=202)
async def telemetry_click(
    event: ClickEvent,
    current_user: str = Depends(get_current_user)
):
    

    
    if not event.url or not event.page_context:
        raise HTTPException(
            status_code=422,
            detail="url and page_context are required and cannot be empty"
        )

    
    publish_event(event.model_dump(mode="json"))

    
    return {"status": 202, "message": "Event queued for background processing"}