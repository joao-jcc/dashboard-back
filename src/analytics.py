import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from src.models import EventSummary, EventDetails
from src.csv_loader import CSVLoader

csv_loader = CSVLoader()

class EventAnalytics:
    def __init__(self):
        self.loader = csv_loader

    def get_events_summary(self) -> List[EventSummary]:
        events_df = self.loader.events
        events_summary = []
        for _, event in events_df.iterrows():
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
        events_df = self.loader.events
        event_row = events_df[events_df['id'] == event_id]
        if event_row.empty:
            return None
        event_data = event_row.iloc[0].to_dict()

        inscriptions_df = self.loader.inscricaos
        inscriptions_df = inscriptions_df[inscriptions_df['evento_id'] == event_id]

        transactions_df = self.loader.transactions
        transactions_df = transactions_df[transactions_df['evento_id'] == event_id]

        total_revenue = self._calculate_total_revenue(transactions_df)
        current_inscriptions = len(inscriptions_df)
        goal = int(event_data.get('limit_maximo_inscritos', 0))
        ticket_price = self._calculate_ticket_price(transactions_df)

        created_at = pd.to_datetime(event_data['created_at'])
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        days_remaining = max(0, (start_date - today).days)
        is_active = today < start_date

        average_inscriptions = self._calculate_average_inscriptions(event_data, inscriptions_df)
        daily_target = self._calculate_daily_target(event_data, inscriptions_df)

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
        if transactions_df.empty:
            return 0.0
        df = transactions_df.copy()
        df['amount_float'] = df['amount'].astype(str).str.replace(',', '.').astype(float)
        df['signed_amount'] = df['amount_float'] * df['credit'].replace({0: 0, 1: 1})
        return round(df['signed_amount'].sum(), 2)

    def _calculate_average_inscriptions(self, event_data: Dict, inscriptions_df: pd.DataFrame) -> float:
        created_at = pd.to_datetime(event_data['created_at'])
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        total_days = (today - created_at).days if today < start_date else (start_date - created_at).days
        if total_days <= 0:
            return 0.0
        total_inscriptions = len(inscriptions_df)
        return round(total_inscriptions / total_days, 2)

    def _calculate_daily_target(self, event_data: Dict, inscriptions_df: pd.DataFrame) -> float:
        start_date = pd.to_datetime(event_data['data_inicio'])
        today = datetime.now()
        if today >= start_date:
            return 0.0
        days_remaining = (start_date - today).days
        
        # Se não há dias restantes ou é zero, retorna 0
        if days_remaining <= 0:
            return 0.0
            
        current_inscriptions = len(inscriptions_df)
        goal = int(event_data.get('limit_maximo_inscritos', 0))
        remaining_needed = max(0, goal - current_inscriptions)
        return round(remaining_needed / days_remaining, 1)

    def _generate_inscriptions_chart_data(self, event_data: Dict, inscriptions_df: pd.DataFrame) -> Dict[str, List[int]]:
        if inscriptions_df.empty:
            return {"remaining_days": [], "inscriptions": []}

        start_date = pd.to_datetime(event_data['data_inicio'])
        created_at = pd.to_datetime(event_data['created_at'])
        df = inscriptions_df.copy()
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['dias_antecedencia'] = (start_date - df['created_at']).dt.days

        max_days = (start_date - created_at).days
        total_inscriptions = len(df)

        # Cumulative counts por dia
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

    def _generate_revenue_chart_data(self, event_data: Dict, transactions_df: pd.DataFrame) -> Dict[str, List[float]]:
        if transactions_df.empty:
            return {"remaining_days": [], "revenue": []}

        start_date = pd.to_datetime(event_data['data_inicio'])
        created_at = pd.to_datetime(event_data['created_at'])
        df = transactions_df.copy()
        df['created_at'] = pd.to_datetime(df['created_at'], format='mixed', errors='coerce')
        df['amount_float'] = df['amount'].astype(str).str.replace(',', '.').astype(float)
        df['signed_amount'] = df['amount_float'] * df['credit'].replace({0: 0, 1: 1})
        df['dias_antecedencia'] = (start_date - df['created_at']).dt.days

        max_days = (start_date - created_at).days
        days_range = np.arange(0, max_days + 1)

        # Soma diária vetorizada
        daily_revenue = df.groupby('dias_antecedencia')['signed_amount'].sum().reindex(days_range, fill_value=0).values
        cumulative = np.cumsum(daily_revenue[::-1])[::-1] 

        return {
            "remaining_days": days_range.tolist(),
            "revenue": np.round(cumulative, 2).tolist()
        }


    def _calculate_ticket_price(self, transactions_df: pd.DataFrame) -> float:
        if transactions_df.empty:
            return 0.0
        credit_transactions = transactions_df[transactions_df['credit'] == 1]
        if credit_transactions.empty:
            return 0.0
        amounts = credit_transactions['amount'].astype(str).str.replace(',', '.').astype(float)
        return round(amounts.mean(), 2)


    def get_dynamic_fields_distribution(self, event_id: int) -> Dict[str, Dict[str, int]]:
        """
        Analisa a distribuição dos campos dinâmicos de um evento específico usando vetorização pandas
        """
        event_fields_df = self.loader.event_dynamic_fields
        event_fields = event_fields_df[event_fields_df['evento_id'] == event_id]
        if event_fields.empty:
            return {}

        inscriptions_df = self.loader.inscricaos
        event_inscriptions = inscriptions_df[inscriptions_df['evento_id'] == event_id]
        if event_inscriptions.empty:
            return {}

        # Extrai todos os pares chave:valor do campo serial_event_dynamic_fields
        # Exemplo: "100: 25\n120: Masculino\n130: Superior"
        serials = event_inscriptions['serial_event_dynamic_fields'].fillna("")
        # Cria um DataFrame explodido com todas as chaves e valores
        exploded = serials.str.extractall(r"(\d+):\s*([^\n]*)")
        exploded.index = exploded.index.droplevel(1)  # Remove o segundo nível do índice
        exploded.columns = ['field_id', 'field_value']
        exploded['field_id'] = exploded['field_id'].astype(str)
        exploded['field_value'] = exploded['field_value'].str.strip()
        exploded['inscricao_idx'] = exploded.index

        # Junta com os campos dinâmicos do evento
        valid_field_ids = set(str(fid) for fid in event_fields['id'])
        exploded = exploded[exploded['field_id'].isin(valid_field_ids)]

        # Para cada campo, conta os valores
        result = {}
        for _, field in event_fields.iterrows():
            field_id = str(field['id'])
            field_label = field['label']
            # Filtra só os valores deste campo
            field_values = exploded[exploded['field_id'] == field_id]['field_value']
            counts = field_values.value_counts().to_dict()
            # Conta undefined (inscrições que não têm esse campo)
            total_inscr = len(event_inscriptions)
            undefined_count = total_inscr - len(field_values)
            if undefined_count > 0:
                counts['undefined'] = undefined_count
            # Filtrar campos com apenas 1 tipo ou mais de 20 tipos
            unique_types = len(counts)
            if unique_types > 1 and unique_types <= 20:
                result[field_label] = counts
        return result

    def _extract_field_value(self, serial_data: str, field_id: str) -> Optional[str]:
        """
        Extrai o valor de um campo específico do texto serializado
        
        Formato esperado: "1: valor1\n2: valor2\n100: idade_valor\n120: sexo_valor"
        """
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
