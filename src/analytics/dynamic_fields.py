import pandas as pd
from typing import Dict
from src.models import EventDynamicFields


class DynamicFieldsAnalytics:
    def __init__(self, loader):
        self.loader = loader

    def get_dynamic_fields_distribution(self, event_id: int) -> EventDynamicFields:
        event_fields_df = self.loader.get_event_fields(event_id)
        if event_fields_df.empty:
            return EventDynamicFields(labels=[], distribution={})

        inscriptions_df = self.loader.get_event_dynamic_fields(event_id)
        if inscriptions_df.empty:
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
