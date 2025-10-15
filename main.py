"""
FastAPI Dashboard Backend
Main application file for events data API
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from pydantic import BaseModel
import uvicorn
import time
import logging

from src.models import EventSummary, EventInscriptions, EventRevenue, EventDynamicFields
from src.analytics import EventAnalytics
from src.crypto_utils import decrypt


app = FastAPI(
    title="Dashboard Events API",
    description="API for events data and analytics",
    version="1.0.0"
)


# CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     
    allow_credentials=False,  
    allow_methods=["*"],    
    allow_headers=["*"],
)


analytics = EventAnalytics()


@app.get("/")
async def root():
    return {"message": "Dashboard Events API is running"}


@app.get("/api/events/{token}", response_model=Dict[int, EventSummary])
async def get_events(token: str):
    """
    Get all events summary for a specific org using encrypted token
    """
    org_id = int(decrypt(token))
    analytics.set_org_id(org_id=org_id)
    events = analytics.get_events_summary()
    return events


@app.get("/api/events/dynamic-fields/{token}/{event_id}", response_model=EventDynamicFields)
def get_event_dynamic_fields_distribution(token: str, event_id: int):
    """Get dynamic fields distribution for a specific event using encrypted token"""
    org_id = int(decrypt(token))
    analytics.set_org_id(org_id=org_id)
    distribution = analytics.get_dynamic_fields_distribution(event_id)
    return distribution


@app.get("/api/events/inscriptions/{token}/{event_id}", response_model=EventInscriptions)
async def get_event_inscriptions(token: str, event_id: int, request: Request):
    """Get event inscriptions analytics using encrypted token"""
    org_id = int(decrypt(token))
    analytics.set_org_id(org_id=org_id)
    result = analytics.get_event_inscriptions(event_id)
    return result
    

@app.get("/api/events/revenue/{token}/{event_id}", response_model=EventRevenue)
async def get_event_revenue(token: str, event_id: int, request: Request):
    """Retorna a receita total do evento using encrypted token"""
    org_id = int(decrypt(token))
    analytics.set_org_id(org_id=org_id)
    result = analytics.get_event_revenue(event_id)
    return result



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)