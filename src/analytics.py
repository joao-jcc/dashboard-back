"""
Analytics engine for calculating event metrics and chart data
Handles business logic for dashboard statistics
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.models import EventSummary, EventDetails
from src.data_loader import DataLoader


class EventAnalytics:
    """Handles analytics calculations for events dashboard"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
    
    def get_events_summary(self) -> List[EventSummary]:
        """
        Returns EventSummary[] with id, name, created_at, start_date
        For all events
        """
        events_df = self.data_loader.events_df
        
        events_summary = []
        for _, event in events_df.iterrows():
            # Parse created_at and data_inicio from database
            created_at = pd.to_datetime(event['created_at'])
            start_date = pd.to_datetime(event['data_inicio'])
            
            summary = EventSummary(
                id=int(event['id']),
                name=str(event['titulo']),
                created_at=created_at,
                start_date=start_date
            )
            events_summary.append(summary)
        
        return events_summary
    
    def get_event_details(self, event_id: int) -> Optional[EventDetails]:
        """
        Get detailed analytics for a specific event
        Returns EventDetails with charts and metrics
        """
        # Get basic event info
        event_data = self.data_loader.get_event_by_id(event_id)
        if not event_data:
            return None
        
        # Get related data
        inscriptions_df = self.data_loader.get_inscricoes_for_event(event_id)
        payments_df = self.data_loader.get_pagamentos_for_event(event_id)
        
        # Calculate basic metrics
        current_inscriptions = len(inscriptions_df)
        goal = int(event_data.get('limit_maximo_inscritos', 0))
        total_revenue = self._calculate_total_revenue(payments_df)
        ticket_price = self._calculate_ticket_price(payments_df)
        
        # Calculate time-based metrics
        created_at = pd.to_datetime(event_data['created_at'])
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        days_remaining = max(0, (start_date - today).days)
        is_active = today < start_date  # True if event is still active
        
        # Calculate targets
        average_inscriptions = self._calculate_average_inscriptions(event_data, inscriptions_df)
        daily_target = self._calculate_daily_target(event_data, inscriptions_df)
        
        # Generate chart data
        chart_inscriptions = self._generate_inscriptions_chart_data(event_data, inscriptions_df)
        chart_revenue = self._generate_revenue_chart_data(event_data, payments_df)
        
        return EventDetails(
            id=event_id,
            name=str(event_data['titulo']),
            chartDataInscriptions=chart_inscriptions,
            chartDataRevenue=chart_revenue,
            currentInscriptions=current_inscriptions,
            averageInscriptions=average_inscriptions,
            targetInscriptions=goal,
            daysRemaining=days_remaining,
            dailyInscriptionsGoal=daily_target,
            ticketPrice=ticket_price,
            totalRevenue=total_revenue,
            isActive=is_active
        )
    
    def _calculate_total_revenue(self, payments_df: pd.DataFrame) -> float:
        """Calculate total revenue from payments"""
        if payments_df.empty:
            return 0.0

        # Convert amount to float and sum
        total = payments_df['amount'].astype(str).str.replace(',', '.').astype(float).sum()
        return round(total, 2)
    
    def _calculate_average_inscriptions(self, event_data: Dict, inscriptions_df: pd.DataFrame) -> float:
        """Calculate average inscriptions per day for a specific event"""
        # Get event dates
        created_at = pd.to_datetime(event_data['created_at'])
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        
        # Calculate the period in days
        if today < start_date:
            # Event hasn't started yet: use today - created_at
            total_days = (today - created_at).days
        else:
            # Event has started: use start_date - created_at
            total_days = (start_date - created_at).days
        
        # Avoid division by zero
        if total_days <= 0:
            return 0.0
        
        # Use provided inscriptions_df instead of fetching again
        total_inscriptions = len(inscriptions_df)
    
        # Calculate average per day
        return round(total_inscriptions / total_days, 2)
    
    def _calculate_daily_target(self, event_data: Dict, inscriptions_df: pd.DataFrame) -> float:
        """Calculate daily inscription target to reach goal"""
        
        # Get event dates
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        
        # If event has already started/concluded, return 0
        if today >= start_date:
            return 0.0
        
        # Calculate days remaining until event starts
        days_remaining = (start_date - today).days
        if days_remaining <= 0:
            return 0.0
        
        # Use provided data instead of fetching again
        current_inscriptions = len(inscriptions_df)
        goal = int(event_data.get('limit_maximo_inscritos', 0))
        
        # Calculate remaining needed inscriptions
        remaining_needed = max(0, goal - current_inscriptions)
        
        # Calculate daily target
        return round(remaining_needed / days_remaining, 1)
    
    def _generate_inscriptions_chart_data(self, event_data: Dict, inscriptions_df: pd.DataFrame) -> Dict[str, List[int]]:
        """Generate chart data for inscriptions over time based on days before event start"""
        
        if inscriptions_df.empty:
            return {"remaining_days": [], "inscriptions": []}
        
        # Get event dates
        created_at = pd.to_datetime(event_data['created_at'])
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        
        # Calculate maximum days of antecedence (from created_at to start_date)
        max_days_antecedence = (start_date - created_at).days
        
        # Convert inscription dates to datetime
        inscriptions_df = inscriptions_df.copy()
        inscriptions_df['created_at'] = pd.to_datetime(inscriptions_df['created_at'])
        
        # Calculate days of antecedence for each inscription (start_date - inscription_date)
        inscriptions_df['dias_antecedencia'] = (start_date - inscriptions_df['created_at']).dt.days
        
        # Determine the range of days to analyze
        if today < start_date:
            days_remaining = (start_date - today).days
            min_days = max(0, days_remaining)
        else:
            min_days = 0
        
        # Generate chart data (cumulative inscriptions by days of antecedence)
        remaining_days = []
        inscriptions = []
        
        for days in range(max_days_antecedence, min_days - 1, -1):  # From max days down to min_days
            # Count cumulative inscriptions up to this point (days of antecedence >= days)
            count = len(inscriptions_df[inscriptions_df['dias_antecedencia'] >= days])
            remaining_days.append(days)
            inscriptions.append(count)
        
        return {
            "remaining_days": remaining_days,
            "inscriptions": inscriptions
        }
    
    def _generate_revenue_chart_data(self, event_data: Dict, payments_df: pd.DataFrame) -> Dict[str, List[float]]:
        """Generate chart data for revenue over time based on days before event start"""
        
        if payments_df.empty:
            return {"remaining_days": [], "revenue": []}
        
        # Get event dates
        created_at = pd.to_datetime(event_data['created_at'])
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        
        # Calculate maximum days of antecedence (from created_at to start_date)
        max_days_antecedence = (start_date - created_at).days
        
        # Convert payment dates and amounts
        payments_df = payments_df.copy()
        payments_df['created_at_dt'] = pd.to_datetime(payments_df['created_at'])
        payments_df['amount_float'] = payments_df['amount'].astype(str).str.replace(',', '.').astype(float)
        
        # Calculate days of antecedence for each payment (start_date - payment_date)
        payments_df['dias_antecedencia'] = (start_date - payments_df['created_at_dt']).dt.days
        
        # Determine the range of days to analyze
        if today < start_date:
            # Event hasn't started yet: go from max_days to days_remaining
            days_remaining = (start_date - today).days
            min_days = max(0, days_remaining)
        else:
            # Event has started/ended: go from max_days to 0
            min_days = 0
        
        # Generate chart data (cumulative revenue by days of antecedence)
        remaining_days = []
        revenues = []
        
        for days in range(max_days_antecedence, min_days - 1, -1):  # From max days down to min_days
            # Sum cumulative revenue up to this point (days of antecedence >= days)
            revenue = payments_df[payments_df['dias_antecedencia'] >= days]['amount_float'].sum()
            remaining_days.append(days)
            revenues.append(round(revenue, 2))
        
        return {
            "remaining_days": remaining_days,
            "revenue": revenues
        }
    
    def _calculate_ticket_price(self, payments_df: pd.DataFrame) -> float:
        """Calculate ticket price for an event based on successful payments"""
        
        # Calculate average from successful payments
        if payments_df.empty:
            return 0.0
   
        amounts = payments_df['amount'].astype(str).str.replace(',', '.').astype(float)
        
        return round(amounts.mean(), 2)
      