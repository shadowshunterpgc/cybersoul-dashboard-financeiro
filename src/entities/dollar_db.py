import sqlite3
import logging

from src.model.currency import CurrencyQuoteModel

DB_PATH = './data/db/dollar.db'
SQL_PATH = './data/sql/finance.sql'


def connect_db():
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")


def create_tables(conn):
    try:
        with open(SQL_PATH, 'r') as file:
            script = file.read()
        conn.executescript(script)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao criar tabela: {e}")


def save_dollar(quote: CurrencyQuoteModel):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dollar (code, codein, name, high, low, varBid, pctChange, bid, ask, date_hour)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quote.code,
            quote.codein,
            quote.name,
            float(quote.high),
            float(quote.low),
            float(quote.varBid),
            float(quote.pctChange),
            float(quote.bid),
            float(quote.ask),
            quote.date
        ))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao salvar cotação: {e}")


def get_dollar(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dollar ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result
    except sqlite3.Error as e:
        logging.error(f"Erro ao obter cotação: {e}")


def get_daily_dollar():
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT bid, date_hour FROM dollar ORDER BY bid DESC")
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        logging.error(f"Erro ao obter cotação do dia todo: {e}")


def init_db():
    conn = connect_db()
    if conn is not None:
        create_tables(conn)
        get_dollar(conn)
        conn.close()
    else:
        logging.error("Falha ao conectar ao banco de dados")


if __name__ == "__main__":
    init_db()
    df = get_daily_dollar()
    print(df['bid'])

