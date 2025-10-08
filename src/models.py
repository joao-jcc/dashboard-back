"""
Pydantic models for the Dashboard Events API
Based on TypeScript interfaces from the frontend
"""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict


class EventSummary(BaseModel):
    """Basic event information for sidebar listing"""
    id: int
    name: str
    created_at: datetime 
    start_date: datetime


class EventDetails(BaseModel):
    """Complete event details with analytics data"""
    id: int
    name: str
    chartDataInscriptions: Dict[str, List[int]] 
    chartDataRevenue: Dict[str, List[float]] 
    currentInscriptions: int           # Current number of enrollments
    averageInscriptions: float
    targetInscriptions: int             # Target inscriptions (limit_maximo_inscritos)
    daysRemaining: int                 # Days until event
    dailyInscriptionsGoal: float       # Daily target to reach goal
    ticketPrice: float                 # Event ticket price
    totalRevenue: float                # Total revenue generated
    isActive: bool                     # True if event is still active (today < start_date)


class ApiError(BaseModel):
    """API Error response"""
    message: str
    code: Optional[str] = None
    status: Optional[int] = None