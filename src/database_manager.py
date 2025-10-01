"""
Database manager for direct database connections
Handles database queries and connection management for events data
"""

import mysql.connector
import os
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


class DatabaseManager:
    """Manages database connections and queries for the dashboard"""
    
    ORG_ID = 17881  # Dunamis Id
    
    def __init__(self):
        self.config = {
            'host': 'aws.connect.psdb.cloud',
            'port': 3306,
            'database': 'ei',
            'user': os.getenv('USER_DATABASE_EINSC'),
            'password': os.getenv('PASSWORD_DATABASE_EINSC'),
            'ssl_disabled': False
        }
        self._connection = None
        self._cursor = None
    
    def connect(self):
        """Establish database connection"""
        self._connection = mysql.connector.connect(**self.config)
        self._connection.autocommit = True
        self._cursor = self._connection.cursor(dictionary=True)

    def disconnect(self):
        """Close database connection and clean up resources"""
        try:
            if self._cursor:
                self._cursor.close()
                self._cursor = None
            if self._connection:
                self._connection.close()
                self._connection = None
        except Exception as e:
            pass  # Silently ignore disconnection errors
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        if not self._connection or not self._connection.is_connected():
            self.connect()
    
    def get_events_for_organization(self) -> List[Dict]:
        """Get all events for the organization"""
        self._ensure_connection()
        
        query = """
        SELECT id, titulo, tipo, created_at, data_inicio, limit_maximo_inscritos, occupied_vacancies, igreja_id 
        FROM eventos 
        WHERE igreja_id = %s
        ORDER BY LOWER(titulo)
        """
        
        self._cursor.execute(query, (self.ORG_ID,))
        events = self._cursor.fetchall()
        return events
      
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict]:
        """Get a specific event by ID"""
        self._ensure_connection()
        
        query = """
        SELECT id, titulo, created_at, data_inicio, limit_maximo_inscritos, igreja_id 
        FROM eventos 
        WHERE id = %s AND igreja_id = %s
        """
        start_time = time.time()
        self._cursor.execute(query, (event_id, self.ORG_ID))
        event = self._cursor.fetchone()
 
        return event
    
    
    def get_inscricoes_for_event(self, event_id: int) -> List[Dict]:
        """Get all inscriptions for a specific event"""
        self._ensure_connection()

        query = """
        SELECT id, inscrito_id, evento_id, status, created_at 
        FROM inscricaos 
        WHERE evento_id = %s AND status = 'Ok'
        """
        
        self._cursor.execute(query, (event_id,))
        inscricoes = self._cursor.fetchall()

        return inscricoes

    
    def get_transactions_for_event(self, event_id: int) -> List[Dict]:
        """Get all transactions for a specific event based on valid enrollments"""
        self._ensure_connection()
        
        query = """
        SELECT t.id, t.enrollment_id, t.amount, t.credit, t.counts_for, t.created_at
        FROM transactions t
        WHERE t.enrollment_id IN (
            SELECT i.id
            FROM inscricaos i
            WHERE i.evento_id = %s
              AND i.status = 'OK'
        )
        AND t.counts_for IN ('both', 'organization_only')
        """
        
        self._cursor.execute(query, (event_id,))
        transactions = self._cursor.fetchall()

        return transactions
    
    def get_total_revenue_for_event(self, event_id: int) -> float:
        """Calculate total revenue for an event using optimized SQL query - only credits"""
        self._ensure_connection()
        
        # Query para somar apenas créditos (credit = TRUE)
        query = """
        SELECT COALESCE(SUM(t.amount), 0) as total_revenue
        FROM transactions t
        INNER JOIN inscricaos i ON t.enrollment_id = i.id
        WHERE i.evento_id = %s 
          AND t.credit = TRUE 
          AND t.counts_for IN ('both', 'organization_only')
        """
        
        # Executar a query
        self._cursor.execute(query, (event_id,))
        result = self._cursor.fetchone()
        total_revenue = float(result['total_revenue']) if result else 0.0
        
        return total_revenue
    

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.disconnect()