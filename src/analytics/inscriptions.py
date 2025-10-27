import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from src.models import EventInscriptions


class InscriptionsAnalytics:
    def __init__(self, loader):
        self.loader = loader

    def get_event_inscriptions(self, event_id: int) -> EventInscriptions:
        inscriptions_df = self.loader.get_event_inscriptions(event_id)
        if inscriptions_df.empty:
            return EventInscriptions(
                id=str(event_id),
                chartDataInscriptions={"remaining_days": [], "inscriptions": []},
                currentInscriptions=0,
                averageInscriptions=0.0,
                targetInscriptions=0
            )

        event_df = self.loader.get_event_by_id(event_id)
        event_data = event_df.iloc[0]

        current_inscriptions = len(inscriptions_df)
        average_inscriptions = self._calculate_average_inscriptions(event_data, current_inscriptions)
        target_inscriptions = int(event_data.get('target_inscriptions', 0))
        chart_inscriptions = self._generate_inscriptions_chart_data(event_data, inscriptions_df)

        return EventInscriptions(
            id=str(event_id),
            chartDataInscriptions=chart_inscriptions,
            currentInscriptions=current_inscriptions,
            averageInscriptions=average_inscriptions,
            targetInscriptions=target_inscriptions
        )

    def _calculate_average_inscriptions(self, event_data: Dict, current_inscriptions: int) -> float:
        created_at = pd.to_datetime(event_data.created_at)
        start_date = pd.to_datetime(event_data.start_date)
        end_period = min(datetime.now(), start_date)
        total_days = (end_period - created_at).days
        if total_days <= 0:
            return 0.0
        return round(current_inscriptions / total_days, 2)

    def _generate_inscriptions_chart_data(self, event_data: Dict, inscriptions_df: pd.DataFrame) -> Dict[str, List[int]]:
        if inscriptions_df.empty:
            return {"remaining_days": [], "inscriptions": []}

        start_date = pd.to_datetime(event_data['start_date'])
        created_at = pd.to_datetime(event_data['created_at'])
        df = inscriptions_df.copy()

        df['created_at'] = pd.to_datetime(df['created_at'])
        df['dias_antecedencia'] = (start_date - df['created_at']).dt.days

        max_days = (start_date - created_at).days
        total_inscriptions = len(df)

        counts = df['dias_antecedencia'].value_counts().sort_index(ascending=False)
        days_range = np.arange(max_days, -1, -1)
        cumulative = np.zeros_like(days_range)

        cum_sum = 0
        for i, day in enumerate(days_range):
            if day in counts:
                cum_sum += counts[day]
            cumulative[i] = cum_sum

        if len(cumulative) > 0:
            cumulative[-1] = total_inscriptions

        return {"remaining_days": days_range.tolist(), "inscriptions": cumulative.tolist()}
