import mysql.connector
import os
import pandas as pd
from typing import List, Dict, Optional
from .settings import DATABASE_CONFIG, DATABASE_MIRROR_CONFIG


class DatabaseManager:
    def __init__(self, org_id: Optional[int] = None):
        self.org_id = org_id
        self.config = DATABASE_CONFIG
        self._connection = None
        self._cursor = None

    # -------------------------------------------------
    # Connection management
    # -------------------------------------------------
    def connect(self):
        self._connection = mysql.connector.connect(**self.config)
        self._connection.autocommit = True
        self._cursor = self._connection.cursor(dictionary=True)

    def disconnect(self):
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()

    def _ensure_connection(self):
        if not self._connection or not self._connection.is_connected():
            self.connect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    # -------------------------------------------------
    # Query — Eventos da organização
    # -------------------------------------------------
    def get_events_for_org(self) -> pd.DataFrame:
        """
        Retorna todos os eventos de uma organização (igreja).
        Ideal para listas e metadados básicos.
        """
        self._ensure_connection()

        query = """
        SELECT
            e.id AS id,
            e.titulo AS name,
            e.data_inicio AS start_date,
            e.created_at AS created_at,
            e.limit_maximo_inscritos AS target_inscriptions
        FROM eventos e
        WHERE e.igreja_id = %s
        ORDER BY LOWER(e.titulo)
        """

        self._cursor.execute(query, (self.org_id,))
        rows = self._cursor.fetchall()
        df = pd.DataFrame(rows)

        return df
    

    def get_event_by_id(self, event_id: int) -> pd.DataFrame:
        """
        Retorna os dados de um evento específico pelo evento_id.
        """
        self._ensure_connection()
        query = """
        SELECT
            e.id AS id,
            e.titulo AS name,
            e.data_inicio AS start_date,
            e.created_at AS created_at,
            e.limit_maximo_inscritos AS target_inscriptions
        FROM eventos e
        WHERE e.id = %s
        """
        self._cursor.execute(query, (event_id,))
        rows = self._cursor.fetchall()
        df = pd.DataFrame(rows)
        return df
    
    
        
    def get_event_inscriptions(self, event_id: int) -> pd.DataFrame:
        """
        Retorna todas as inscrições de um evento específico
        """
        self._ensure_connection()
        query = """
        SELECT created_at
        FROM inscricaos
        WHERE evento_id = %s AND status IN ('Ok', 'Pendente') AND canceled = 0
        ORDER BY created_at ASC
        """
        self._cursor.execute(query, (event_id,))
        rows = self._cursor.fetchall()
        df = pd.DataFrame(rows)

        return df
    

    # -------------------------------------------------
    # Query — Dados detalhados de um evento
    # -------------------------------------------------
    def get_event_transactions_data(self, event_id: int) -> pd.DataFrame:
            """
            Retorna um DataFrame com dados de transações (valor, crédito e data)
            de um evento específico.
            """
            self._ensure_connection()

            query = """
            SELECT
                t.amount,
                t.credit,
                t.created_at AS transaction_date
            FROM transactions AS t
            WHERE t.enrollment_id IN (
                SELECT id
                FROM inscricaos
                WHERE evento_id = %s
                AND status IN ('Ok', 'Pendente')
                AND canceled = 0
            )
            AND t.counts_for IN ('both', 'organization_only')
            ORDER BY t.created_at ASC;
            """

            self._cursor.execute(query, (event_id,))
            rows = self._cursor.fetchall()
            df = pd.DataFrame(rows)

            return df

    # ------------------------------------------------------
    # Query — Campos dinâmicos das inscrições de um evento
    # ------------------------------------------------------
    def get_event_dynamic_fields(self, event_id: int) -> pd.DataFrame:
        """
        Retorna todos os campos dinâmicos serializados das inscrições de um evento específico.
        """
        self._ensure_connection()

        query = """
        SELECT
            serial_event_dynamic_fields
        FROM inscricaos
        WHERE evento_id = %s
          AND status IN ('Ok', 'Pendente')
          AND canceled = 0
        ORDER BY created_at ASC
        """

        self._cursor.execute(query, (event_id,))
        rows = self._cursor.fetchall()
        df = pd.DataFrame(rows)

        return df
    
    def get_event_fields(self, event_id: int) -> pd.DataFrame:
        """
        Retorna os campos dinâmicos definidos para um evento específico.
        """
        self._ensure_connection()
        query = """
        SELECT id, label FROM event_dynamic_fields WHERE evento_id = %s ORDER BY id ASC
        """
        
        self._cursor.execute(query, (event_id,))
        rows = self._cursor.fetchall()
        df = pd.DataFrame(rows)
        
        return df
    