import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.models import EventRevenue


class RevenueAnalytics:
    def __init__(self, loader):
        self.loader = loader

    def get_event_revenue(self, event_id: int) -> EventRevenue:
        event_df = self.loader.get_event_by_id(event_id)
        transactions_df = self.loader.get_event_transactions_data(event_id)

        if event_df.empty or transactions_df.empty:
            return EventRevenue(
                id=str(event_id),
                chartDataRevenue={"remaining_days": [], "revenue": []},
                ticketPrice=0.0,
                totalRevenue=0.0
            )

        event_data = event_df.iloc[0]
        transactions_df = self._prepare_transactions_df(transactions_df, event_data)

        total_revenue = self._calculate_total_revenue(transactions_df)
        chart_data = self._generate_revenue_chart_data(event_data, transactions_df)
        ticket_price = self._calculate_ticket_price(transactions_df)

        return EventRevenue(
            id=str(event_id),
            chartDataRevenue=chart_data,
            ticketPrice=ticket_price,
            totalRevenue=total_revenue
        )

    def _calculate_total_revenue(self, transactions_df: pd.DataFrame) -> float:
        return round(transactions_df['signed_amount'].sum(), 2)

    def _generate_revenue_chart_data(self, event_data: Dict, transactions_df: pd.DataFrame) -> Dict[str, List[float]]:
        start_date = pd.to_datetime(event_data['start_date'])
        created_at = pd.to_datetime(event_data['created_at'])
        max_days = (start_date - created_at).days
        days_range = np.arange(0, max_days + 1)
        daily_revenue = transactions_df.groupby('dias_antecedencia')['signed_amount'].sum().reindex(days_range, fill_value=0).values
        cumulative = np.cumsum(daily_revenue[::-1])[::-1]

        return {
            "remaining_days": days_range.tolist(),
            "revenue": np.round(cumulative, 2).tolist()
        }

    def _calculate_ticket_price(self, transactions_df: pd.DataFrame) -> float:
        df = transactions_df[transactions_df['credit'] == 1]
        if df.empty:
            return 0.0
        return round(df['amount_float'].mean(), 2)

    def _prepare_transactions_df(self, transactions_df: pd.DataFrame, event_data: Optional[Dict] = None) -> pd.DataFrame:
        df = transactions_df.copy()
        df = df.dropna(subset=['amount', 'credit', 'transaction_date'])

        df['amount_float'] = pd.to_numeric(df['amount'].astype(str).str.replace(',', '.'), errors='coerce')
        df['signed_amount'] = df['amount_float'] * df['credit'].replace({0: -1, 1: 1})
        df['created_at'] = pd.to_datetime(df['transaction_date'], format='mixed', errors='coerce')
        if event_data is not None:
            df['dias_antecedencia'] = pd.to_datetime(event_data['start_date']) - df['created_at']
            df['dias_antecedencia'] = df['dias_antecedencia'].dt.days

            
        return df
