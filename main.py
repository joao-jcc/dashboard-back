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
from src.analytics.analytics import EventAnalytics
from src.crypto_utils import decrypt, encode_id, decode_id


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


@app.get("/api/events/{token}", response_model=Dict[str, EventSummary])
async def get_events(token: str):
    """
    Get all events summary for a specific org using encrypted token
    """
    org_id = int(decrypt(token))
    analytics.set_org_id(org_id=org_id)
    events = analytics.get_events_summary()
    
    # Encode os IDs dos eventos antes de enviar para o frontend
    encoded_events = {}
    for real_id, event in events.items():
        encoded_id = encode_id(real_id)
        event.id = encoded_id  # Substitui o ID real pelo encoded
        encoded_events[encoded_id] = event
    
    return encoded_events


@app.get("/api/events/dynamic-fields/{token}/{event_id}", response_model=EventDynamicFields)
def get_event_dynamic_fields_distribution(token: str, event_id: str):
    """Get dynamic fields distribution for a specific event using encrypted token"""
    org_id = int(decrypt(token))
    # Decode o event_id recebido do frontend
    real_event_id = decode_id(event_id)
    analytics.set_org_id(org_id=org_id)
    distribution = analytics.get_dynamic_fields_distribution(real_event_id)
    return distribution


@app.get("/api/events/inscriptions/{token}/{event_id}", response_model=EventInscriptions)
async def get_event_inscriptions(token: str, event_id: str):
    """Get event inscriptions analytics using encrypted token"""
    org_id = int(decrypt(token))
    # Decode o event_id recebido do frontend
    real_event_id = decode_id(event_id)
    analytics.set_org_id(org_id=org_id)
    result = analytics.get_event_inscriptions(real_event_id)
    # Manter o ID encoded na resposta
    result.id = event_id
    return result
    

@app.get("/api/events/revenue/{token}/{event_id}", response_model=EventRevenue)
async def get_event_revenue(token: str, event_id: str):
    """Retorna a receita total do evento using encrypted token"""
    org_id = int(decrypt(token))
    # Decode o event_id recebido do frontend
    real_event_id = decode_id(event_id)
    print(f"REAL EVENT: {real_event_id}")
    analytics.set_org_id(org_id=org_id)
    result = analytics.get_event_revenue(real_event_id)
    # Manter o ID encoded na resposta
    result.id = event_id
    return result



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)