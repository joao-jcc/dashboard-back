import pandas as pd
from typing import Dict, Optional
from src.models import EventSummary, EventRevenue, EventInscriptions, EventDynamicFields
from src.database.database_manager import DatabaseManager
from .revenue import RevenueAnalytics
from .inscriptions import InscriptionsAnalytics
from .dynamic_fields import DynamicFieldsAnalytics


class EventAnalytics:
    def __init__(self, org_id: Optional[int] = 17881):
        self.org_id = org_id
        self.loader = DatabaseManager(org_id=org_id)

        # Submódulos especializados
        self.revenue_analytics = RevenueAnalytics(self.loader)
        self.inscriptions_analytics = InscriptionsAnalytics(self.loader)
        self.dynamic_fields_analytics = DynamicFieldsAnalytics(self.loader)

    def set_org_id(self, org_id: int):
        self.org_id = org_id
        self.loader.org_id = org_id

    def get_events_summary(self) -> Dict[int, EventSummary]:
        events_df = self.loader.get_events_for_org()
        if events_df.empty:
            return {}

        events_df['created_at'] = pd.to_datetime(events_df['created_at'])
        events_df['start_date'] = pd.to_datetime(events_df['start_date'])

        events_dict = {}
        for _, row in events_df.iterrows():
            event_summary = EventSummary(
                id=str(row['id']),
                name=row['name'],
                created_at=row['created_at'],
                start_date=row['start_date'],
                target_inscriptions=row['target_inscriptions']
            )
            events_dict[row['id']] = event_summary

        return events_dict

    def get_event_inscriptions(self, event_id: int) -> EventInscriptions:
        return self.inscriptions_analytics.get_event_inscriptions(event_id)

    def get_event_revenue(self, event_id: int) -> EventRevenue:
        return self.revenue_analytics.get_event_revenue(event_id)

    def get_dynamic_fields_distribution(self, event_id: int) -> EventDynamicFields:
        return self.dynamic_fields_analytics.get_dynamic_fields_distribution(event_id)
