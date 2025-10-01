import mysql.connector
import os
import pandas as pd

ORG_ID = 17881
BATCH_SIZE = 10000


def connect_db():
    """Conecta ao banco de dados e retorna conexão e cursor."""
    from dotenv import load_dotenv

    load_dotenv()
    config = {
        "host": "aws.connect.psdb.cloud",
        "port": 3306,
        "database": "ei",
        "user": os.getenv("USER_DATABASE_EINSC"),
        "password": os.getenv("PASSWORD_DATABASE_EINSC"),
        "ssl_disabled": False,
    }
    conn = mysql.connector.connect(**config)
    conn.autocommit = True
    cursor = conn.cursor(dictionary=True)
    return conn, cursor


def export_data(cursor, sql_query_template, batch_size, file_name, id_column, table_alias="i", directory="data"):
    """Exporta dados em batches paginados para CSV"""
    os.makedirs(directory, exist_ok=True)
    full_path = os.path.join(directory, file_name)

    last_id = 0
    if os.path.exists(full_path):
        df_existing = pd.read_csv(full_path)
        if not df_existing.empty:
            last_id = df_existing[id_column].max()

    first_write = last_id == 0

    while True:
        last_id_filter = f"AND {table_alias}.{id_column} > {last_id}" if last_id > 0 else ""
        paginated_query = sql_query_template.format(org_id=ORG_ID, last_id_filter=last_id_filter)
        paginated_query += f" ORDER BY {table_alias}.{id_column} ASC LIMIT {batch_size}"

        cursor.execute(paginated_query)
        results = cursor.fetchall()
        if not results:
            break

        df = pd.DataFrame(results)
        column_names = [i[0] for i in cursor.description]
        df.columns = column_names

        if first_write:
            df.to_csv(full_path, index=False, mode="w")
            first_write = False
        else:
            df.to_csv(full_path, index=False, header=False, mode="a")

        last_id = df.iloc[-1][id_column]


def export_events(cursor, batch_size=BATCH_SIZE, directory="data"):
    sql_query_template = (
        "SELECT e.id AS id, e.titulo, e.tipo, e.created_at, e.data_inicio, "
        "e.limit_maximo_inscritos, e.occupied_vacancies, e.igreja_id "
        "FROM eventos e "
        "WHERE e.igreja_id = {org_id} {last_id_filter}"
    )
    export_data(cursor, sql_query_template, batch_size, "events.csv", id_column="id", table_alias="e", directory=directory)


def export_inscricaos(cursor, batch_size=BATCH_SIZE, directory="data"):
    sql_query_template = (
        "SELECT i.id AS id, i.inscrito_id, i.evento_id, i.status, i.created_at "
        "FROM inscricaos i "
        "JOIN eventos e ON e.id = i.evento_id "
        "WHERE e.igreja_id = {org_id} {last_id_filter}"
    )
    export_data(cursor, sql_query_template, batch_size, "inscricaos.csv", id_column="id", table_alias="i", directory=directory)


def export_transactions(cursor, batch_size=BATCH_SIZE, directory="data"):
    sql_query_template = (
        "SELECT t.id AS id, t.enrollment_id, t.amount, t.credit, "
        "t.counts_for, t.created_at, i.evento_id "
        "FROM transactions t "
        "JOIN inscricaos i ON i.id = t.enrollment_id "
        "JOIN eventos e ON e.id = i.evento_id "
        "WHERE e.igreja_id = {org_id} "
        "AND t.counts_for IN ('both', 'organization_only') "
        "{last_id_filter}"
    )
    export_data(cursor, sql_query_template, batch_size, "transactions.csv", id_column="id", table_alias="t", directory=directory)


if __name__ == "__main__":
    conn, cursor = connect_db()
    export_events(cursor)
    export_inscricaos(cursor)
    export_transactions(cursor)
    cursor.close()
    conn.close()
