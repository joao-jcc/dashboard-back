import mysql.connector
import os
import pandas as pd
from dotenv import load_dotenv    

load_dotenv()

def connect_to_db():
    config = {
        'host': 'aws.connect.psdb.cloud',
        'port': 3306,
        'database': 'ei',
        'user': os.getenv('USER_DATABASE_EINSC'),
        'password': os.getenv('PASSWORD_DATABASE_EINSC'),
        'ssl_disabled': False
    }
    conn = mysql.connector.connect(**config)
    conn.autocommit = True
    cursor = conn.cursor()
    return conn, cursor

def get_data(cursor, sql_query, batch_size, file_name, id_column):
    last_id = 0
    full_path = file_name
    first_write = True

    while True:
        cursor.execute(sql_query + f" WHERE {id_column} > {last_id} ORDER BY {id_column} ASC LIMIT {batch_size}")
        results = cursor.fetchall()
        if not results:
            break
        df = pd.DataFrame(results)
        column_names = [i[0] for i in cursor.description]
        df.columns = column_names
        if first_write:
            df.to_csv(full_path, index=False, mode='w')
            first_write = False
        else:
            df.to_csv(full_path, index=False, header=False, mode='a')
        last_id = df.iloc[-1][0]
        print(f"Downloaded up to id {last_id}")

    print(f"Data saved to {full_path}")

def search_events(cursor, batch_size):
    sql_query = "SELECT id, titulo, tipo, created_at, data_inicio, limit_maximo_inscritos, occupied_vacancies, igreja_id FROM eventos"
    get_data(cursor, sql_query, batch_size, 'events.csv', id_column="id")

def search_igrejas(cursor, batch_size):
    sql_query = "SELECT id, nome, cidade, estado, bairro, cep FROM igrejas"
    get_data(cursor, sql_query, batch_size, 'igrejas.csv', id_column="id")

def search_inscricaos(cursor, batch_size):
    sql_query = "SELECT id, inscrito_id, evento_id, status, created_at FROM inscricaos"
    get_data(cursor, sql_query, batch_size, 'inscricaos.csv', id_column="id")

def search_pagamentos(cursor, batch_size):
    sql_query = "SELECT id, status, amount, payment_type, evento_id, additional_value, created_at FROM pagamentos"
    get_data(cursor, sql_query, batch_size, 'pagamentos.csv', id_column="id")


def search_modalidade_pagamentos(cursor, batch_size):
    sql_query = "SELECT id, valor, evento_id FROM modalidade_pagamentos"
    get_data(cursor, sql_query, batch_size, 'modalidade_pagamentos.csv', id_column="id")


if __name__ == '__main__':
    conn, cursor = connect_to_db()
    search_events(cursor, 10000)
    cursor.close()
    conn.close()
