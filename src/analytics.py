import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from src.models import EventSummary, EventInscriptions, EventRevenue, EventDynamicFields
from src.database_manager import DatabaseManager 

class EventAnalytics:
    def __init__(self, org_id: Optional[int] = 17881):
        self.org_id = org_id
        self.loader = DatabaseManager(org_id=org_id)

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
                id=row['id'],
                name=row['name'],
                created_at=row['created_at'],
                start_date=row['start_date'],
                target_inscriptions=row['target_inscriptions']
            )
            events_dict[row['id']] = event_summary

        return events_dict
    

    def get_event_inscriptions(self, event_id: int) -> Optional[EventInscriptions]:
        inscriptions_df = self.loader.get_event_inscriptions(event_id)
        if inscriptions_df.empty:
            return EventInscriptions(
                id=event_id,
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
            id=event_id,
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

    def _calculate_daily_target(self, event_data: Dict, current_inscriptions: int) -> float:
        start_date = pd.to_datetime(event_data['start_date'])
        today = datetime.now()
        if today >= start_date:
            return 0.0
            
        days_remaining = (start_date - today).days
        if days_remaining <= 0:
            return 0.0
            
        goal = int(event_data.get('max_participants', 0))
        remaining_needed = max(0, goal - current_inscriptions)
        
        return round(remaining_needed / days_remaining, 1)

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

    def get_event_revenue(self, event_id: int) -> EventRevenue:
        """
        Retorna um objeto EventRevenue completo, usando a função auxiliar para preparar o DataFrame.
        """
        event_df = self.loader.get_event_by_id(event_id)
        if event_df.empty:
            return EventRevenue(id=event_id, chartDataRevenue={"remaining_days": [], "revenue": []}, ticketPrice=0.0, totalRevenue=0.0)

        event_data = event_df.iloc[0]
        transactions_df = self.loader.get_event_transactions_data(event_id)
        
        # Limpa e prepara o DataFrame usando a função auxiliar
        transactions_df = self._prepare_transactions_df(transactions_df, event_data)
        
        # Filtra apenas transações de crédito após preparar os dados
        transactions_df = transactions_df[transactions_df['credit'] == 1]

        # Passa o DataFrame por referência para as funções auxiliares
        total_revenue = self._calculate_total_revenue(transactions_df)
        chart_data = self._generate_revenue_chart_data(event_data, transactions_df)
        ticket_price = self._calculate_ticket_price(transactions_df)

        return EventRevenue(
            id=event_id,
            chartDataRevenue=chart_data,
            ticketPrice=ticket_price,
            totalRevenue=total_revenue
        )


    def _calculate_total_revenue(self, transactions_df: pd.DataFrame) -> float:
        if transactions_df.empty:
            return 0.0
        return round(transactions_df['signed_amount'].sum(), 2)
        
    def _generate_revenue_chart_data(self, event_data: Dict, transactions_df: pd.DataFrame) -> Dict[str, List[float]]:
        if transactions_df.empty:
            return {"remaining_days": [], "revenue": []}
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
        if transactions_df.empty:
            return 0.0
        if transactions_df.empty:
            return 0.0
        return round(transactions_df['amount_float'].mean(), 2)


    def _prepare_transactions_df(self, transactions_df: pd.DataFrame, event_data: Optional[Dict] = None) -> pd.DataFrame:
        """
        Limpa e prepara o DataFrame de transações para os cálculos de receita.
        Se event_data for fornecido, calcula 'dias_antecedencia'.
        """
        # Handle empty DataFrame
        if transactions_df.empty:
            df = pd.DataFrame(columns=['amount', 'credit', 'transaction_date', 'amount_float', 'signed_amount', 'created_at'])
            if event_data is not None:
                df['dias_antecedencia'] = pd.Series(dtype='int64')
            return df
        
        df = transactions_df.copy()
        
        # Ensure required columns exist
        if 'amount' not in df.columns:
            df['amount'] = '0.0'
        if 'credit' not in df.columns:
            df['credit'] = 0
        if 'transaction_date' not in df.columns:
            df['transaction_date'] = pd.NaT
        
        df['amount'] = df['amount'].fillna('0.0')
        df['credit'] = df['credit'].fillna(0)
        df['amount_float'] = pd.to_numeric(df['amount'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
        df['signed_amount'] = df['amount_float'] * df['credit'].replace({0: -1, 1: 1})
        df['created_at'] = pd.to_datetime(df['transaction_date'], format='mixed', errors='coerce')
        if event_data is not None:
            df['dias_antecedencia'] = pd.to_datetime(event_data['start_date']) - df['created_at']
            df['dias_antecedencia'] = df['dias_antecedencia'].dt.days
        return df


    def get_dynamic_fields_distribution(self, event_id: int):
        event_fields_df = self.loader.get_event_fields(event_id)
        if event_fields_df.empty:
            return EventDynamicFields(labels=[], distribution={})

        inscriptions_df = self.loader.get_event_dynamic_fields(event_id)
        if inscriptions_df.empty:
            # Return empty distribution for all fields
            labels = [field['label'] for _, field in event_fields_df.iterrows()]
            return EventDynamicFields(labels=labels, distribution={})

        serials = inscriptions_df['serial_event_dynamic_fields'].fillna("")
        exploded = serials.str.extractall(r"(\d+):\s*([^\n]*)")
        exploded.index = exploded.index.droplevel(1)
        exploded.columns = ['field_id', 'field_value']
        exploded['field_id'] = exploded['field_id'].astype(str)
        exploded['field_value'] = exploded['field_value'].str.strip()
        exploded['inscricao_idx'] = exploded.index

        valid_field_ids = set(str(fid) for fid in event_fields_df['id'])
        exploded = exploded[exploded['field_id'].isin(valid_field_ids)]

        result = {}
        labels = []
        for _, field in event_fields_df.iterrows():
            field_id = str(field['id'])
            field_label = field['label']
            labels.append(field_label)
            field_values = exploded[exploded['field_id'] == field_id]['field_value']
            counts = field_values.value_counts().to_dict()
            total_inscr = len(inscriptions_df)
            undefined_count = total_inscr - len(field_values)
            if undefined_count > 0:
                counts['undefined'] = undefined_count
            unique_types = len(counts)
            if unique_types > 1 and unique_types <= 20:
                result[field_label] = counts

        return EventDynamicFields(labels=labels, distribution=result)

    def _extract_field_value(self, serial_data: str, field_id: str) -> Optional[str]:
        lines = serial_data.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key == field_id:
                        return value
        return None
