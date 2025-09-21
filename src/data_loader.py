"""
Data loader for CSV files
Handles reading and parsing of events, inscriptions, payments data
"""

import pandas as pd
import os
from typing import Dict, List, Optional
from datetime import datetime


class DataLoader:
    """Loads and manages CSV data for the dashboard"""
    ORG_ID = 17881 # Dunamis Id
    
    def __init__(self, data_dir: str = "database"):
        self.data_dir = data_dir
        self.events_df = None
        self.inscricoes_df = None
        self.pagamentos_df = None
        self._load_data()
        
    def _load_data(self):
        """Load all CSV files into memory and filter by organization ID"""       

        # Load events data filter by organization id
        self.events_df = pd.read_csv(os.path.join(self.data_dir, "events.csv"))
        self.events_df = self.events_df[self.events_df['igreja_id'] == self.ORG_ID]
        

        org_event_ids = set(self.events_df['id'].tolist()) if not self.events_df.empty else set()
        
        # Load inscriptions data and filter by events from this organization
        self.inscricoes_df = pd.read_csv(os.path.join(self.data_dir, "inscricoes.csv"))
        if not org_event_ids:
            self.inscricoes_df = self.inscricoes_df.iloc[0:0]  # Empty DataFrame
        else:
            indexs = (self.inscricoes_df['evento_id'].isin(org_event_ids)) & (self.inscricoes_df['status'] == 'Ok')
            self.inscricoes_df = self.inscricoes_df[indexs]

        
        # Load payments data and filter by events from this organization
        self.pagamentos_df = pd.read_csv(os.path.join(self.data_dir, "pagamentos.csv"))
        if not org_event_ids:
            self.pagamentos_df = self.pagamentos_df.iloc[0:0]  # Empty DataFrame
        else:
            indexs = ((self.pagamentos_df['evento_id'].isin(org_event_ids)) & (self.pagamentos_df['status'].isin(['Compensado', 'Ok', 'Aprovado'])))
            self.pagamentos_df = self.pagamentos_df[indexs]
       
        
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict]:
        """Get a specific event by ID"""
        event_row = self.events_df[self.events_df['id'] == event_id]
        if event_row.empty:
            return None
        return event_row.iloc[0].to_dict()
    
    def get_inscricoes_for_event(self, event_id: int) -> pd.DataFrame:
        """Get all inscriptions for a specific event"""
        return self.inscricoes_df[self.inscricoes_df['evento_id'] == event_id]
    
    def get_pagamentos_for_event(self, event_id: int) -> pd.DataFrame:
        """Get all payments for a specific event"""
        return self.pagamentos_df[self.pagamentos_df['evento_id'] == event_id]