import psycopg


class PgFrame:
    def __init__(self, conn_str):
        self.conn_str = conn_str
        self.conn = psycopg.connect(conn_str)
