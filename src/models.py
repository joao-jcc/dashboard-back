"""
Pydantic models for the Dashboard Events API
Based on TypeScript interfaces from the frontend
"""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict


class EventSummary(BaseModel):
    id: int
    name: str
    created_at: datetime 
    start_date: datetime
    target_inscriptions: int


class EventRevenue(BaseModel):
    id: int
    chartDataRevenue: Dict[str, List[float]] 
    ticketPrice: float     
    totalRevenue: float 


class EventInscriptions(BaseModel):
    id: int
    chartDataInscriptions: Dict[str, List[int]]
    currentInscriptions: int
    averageInscriptions: float
    targetInscriptions: int

class EventDynamicFields(BaseModel):
    labels: List[str]
    distribution: Dict[str, Dict[str, int]]


class ApiError(BaseModel):
    """API Error response"""
    message: str
    code: Optional[str] = None
    status: Optional[int] = None