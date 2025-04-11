import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class StockData:
    id: Optional[int]
    symbol: str
    price: float
    volume: int
    high: float
    low: float
    open: float
    close: float
    date: datetime
    created_at: datetime = datetime.now()

class StockDataRepository:
    def __init__(self, db_path: str = "data/db/stock_market.db"):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        """Create the stock_data table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                open REAL NOT NULL,
                close REAL NOT NULL,
                date TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_symbol_date 
            ON stock_data(symbol, date)
        """)
        
        conn.commit()
        conn.close()

    def save_stock_data(self, stock: StockData):
        """Save stock data to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO stock_data 
            (symbol, price, volume, high, low, open, close, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stock.symbol,
            stock.price,
            stock.volume,
            stock.high,
            stock.low,
            stock.open,
            stock.close,
            stock.date.isoformat()
        ))
        
        conn.commit()
        conn.close()

    def get_stock_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None):
        """Get stock data for a specific symbol and date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM stock_data WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY date DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [StockData(
            id=row[0],
            symbol=row[1],
            price=row[2],
            volume=row[3],
            high=row[4],
            low=row[5],
            open=row[6],
            close=row[7],
            date=datetime.fromisoformat(row[8]),
            created_at=datetime.fromisoformat(row[9])
        ) for row in results]

    def get_latest_stock_price(self, symbol: str) -> Optional[float]:
        """Get the latest stock price for a given symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT price FROM stock_data 
            WHERE symbol = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None 