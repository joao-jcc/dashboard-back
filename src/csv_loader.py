import os
import pandas as pd
import time
import threading
from .export_data import connect_db, export_events, export_inscricaos, export_transactions, export_event_dynamic_fields

class CSVLoader:
    def __init__(self, directory="data", interval_minutes=20):
        self.directory = directory
        self.interval_minutes = interval_minutes
        self.load_csvs()

        # Inicia o clock em uma thread separada
        self._thread = threading.Thread(target=self._clock_loop, daemon=True)
        self._thread.start()

    def load_csvs(self):
        """Carrega os CSVs em memória."""
        self.events = pd.read_csv(os.path.join(self.directory, "events.csv"))
        self.events = self.events.sort_values(by='titulo', key=lambda x: x.str.lower())
        self.inscricaos = pd.read_csv(os.path.join(self.directory, "inscricaos.csv"))
        self.transactions = pd.read_csv(os.path.join(self.directory, "transactions.csv"))
        self.event_dynamic_fields = pd.read_csv(os.path.join(self.directory, "event_dynamic_fields.csv"))

    def _clock_loop(self):
        """Loop interno que atualiza os CSVs periodicamente."""
        while True:
            try:
                conn, cursor = connect_db()

                export_events(cursor)
                export_inscricaos(cursor)
                export_transactions(cursor)
                export_event_dynamic_fields(cursor)

                cursor.close()
                conn.close()

                self.load_csvs()
                print(f"Dados atualizados! Próxima atualização em {self.interval_minutes} minutos.")

            except Exception as e:
                print("Erro durante atualização:", e)

            time.sleep(self.interval_minutes * 60)
