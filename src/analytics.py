"""
Analytics engine for calculating event metrics and chart data
Handles business logic for dashboard statistics
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.models import EventSummary, EventDetails
from src.database_manager import DatabaseManager


class EventAnalytics:
    """Handles analytics calculations for events dashboard"""
    def __init__(self):
        pass

    def get_events_summary(self) -> List[EventSummary]:
        """
        Returns EventSummary[] with id, name, created_at, start_date
        For all events
        """
        with DatabaseManager() as db:
            events = db.get_events_for_organization()
            
            events_summary = []
            for event in events:
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
        with DatabaseManager() as db:
            # Get basic event info
            event_data = db.get_event_by_id(event_id)
            if not event_data:
                return None
            
            # Get related data and convert to DataFrames when needed for analytics
            inscriptions_df = pd.DataFrame(db.get_inscricoes_for_event(event_id))
            
            # Use optimized SQL query for revenue calculation
            total_revenue = db.get_total_revenue_for_event(event_id)
            transactions_df = pd.DataFrame(db.get_transactions_for_event(event_id))

            
            # Calculate basic metrics
            current_inscriptions = len(inscriptions_df)
            goal = int(event_data.get('limit_maximo_inscritos', 0))
            ticket_price = self._calculate_ticket_price(transactions_df)
            
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
            chart_revenue = self._generate_revenue_chart_data(event_data, transactions_df)
            
            result = EventDetails(
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
        
        return result
    
    def _calculate_total_revenue(self, transactions_df: pd.DataFrame) -> float:
        """Calculate total revenue from transactions"""
        if transactions_df.empty:
            return 0.0

        # Convert amount to float
        transactions_df = transactions_df.copy()
        transactions_df['amount_float'] = transactions_df['amount'].astype(str).str.replace(',', '.').astype(float)
        
        # Calculate revenue: sum when credit=1, subtract when credit=0
        revenue = 0.0
        for _, transaction in transactions_df.iterrows():
            amount = transaction['amount_float']
            credit = transaction['credit']
            
            if credit == 1:
                revenue += amount
            else:  # credit == 0
                revenue -= amount
        
        return round(revenue, 2)
    
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
    
    def _generate_revenue_chart_data(self, event_data: Dict, transactions_df: pd.DataFrame) -> Dict[str, List[float]]:
        """Generate chart data for revenue over time based on days before event start"""
        
        if transactions_df.empty:
            return {"remaining_days": [], "revenue": []}
        
        # Get event dates
        created_at = pd.to_datetime(event_data['created_at'])
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        
        # Calculate maximum days of antecedence (from created_at to start_date)
        max_days_antecedence = (start_date - created_at).days
        
        # Convert transaction dates and amounts
        transactions_df = transactions_df.copy()
        transactions_df['created_at_dt'] = pd.to_datetime(transactions_df['created_at'])
        transactions_df['amount_float'] = transactions_df['amount'].astype(str).str.replace(',', '.').astype(float)
        
        # Calculate days of antecedence for each transaction (start_date - transaction_date)
        transactions_df['dias_antecedencia'] = (start_date - transactions_df['created_at_dt']).dt.days
        
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
            # Calculate cumulative revenue up to this point (days of antecedence >= days)
            relevant_transactions = transactions_df[transactions_df['dias_antecedencia'] >= days]
            
            revenue = 0.0
            for _, transaction in relevant_transactions.iterrows():
                amount = transaction['amount_float']
                credit = transaction['credit']
                
                if credit == 1:
                    revenue += amount
                else:  # credit == 0
                    revenue -= amount
            
            remaining_days.append(days)
            revenues.append(round(revenue, 2))
        
        return {
            "remaining_days": remaining_days,
            "revenue": revenues
        }
    
    def _calculate_ticket_price(self, transactions_df: pd.DataFrame) -> float:
        """Calculate ticket price for an event based on successful transactions"""
        
        # Calculate average from successful transactions (credit = 1 only)
        if transactions_df.empty:
            return 0.0
   
        # Filter only credit transactions (income)
        credit_transactions = transactions_df[transactions_df['credit'] == 1]
        
        if credit_transactions.empty:
            return 0.0
        
        amounts = credit_transactions['amount'].astype(str).str.replace(',', '.').astype(float)
        
        return round(amounts.mean(), 2)
      