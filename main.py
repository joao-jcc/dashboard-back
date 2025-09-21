"""
FastAPI Dashboard Backend
Main application file for events data API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from typing import List
from pydantic import BaseModel
import uvicorn
import logging

from src.models import EventSummary, EventDetails
from src.data_loader import DataLoader
from src import analytics
from src.analytics import EventAnalytics
from src.data_loader import DataLoader

# Setup logging
logger = logging.getLogger(__name__)

# Request models
class BulkEventsRequest(BaseModel):
    event_ids: List[int]

app = FastAPI(
    title="Dashboard Events API",
    description="API for events data and analytics",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize data loader and analytics
data_loader = DataLoader()
analytics = EventAnalytics(data_loader)


@app.get("/")
async def root():
    return {"message": "Dashboard Events API is running"}


@app.get("/api/events", response_model=List[EventSummary])
async def get_events():
    """
    Get all events summary
    Returns basic event information for sidebar listing
    """
    try:
        events = analytics.get_events_summary()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading events: {str(e)}")


@app.get("/api/events/{event_id}", response_model=EventDetails)
async def get_event_details(event_id: int):
    """
    Get detailed event information with analytics data
    Used for charts and dashboard cards
    """
   
    event_details = analytics.get_event_details(event_id)
    if not event_details:
        
        raise HTTPException(status_code=404, detail="Event not found")

    return event_details

@app.post("/api/events/bulk")
async def get_multiple_events(request: BulkEventsRequest):
    """Get multiple event details at once for optimization (max 5 events)"""
    try:
        event_ids = request.event_ids
        
        if not event_ids or len(event_ids) > 5:
            raise HTTPException(status_code=400, detail="event_ids list size must be greater than zero and less than five")
        
        
        # Get details for selected events
        results = []
        for event_id in event_ids:
            event_details = analytics.get_event_details(event_id)
            if event_details:
                results.append(event_details)
        
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)