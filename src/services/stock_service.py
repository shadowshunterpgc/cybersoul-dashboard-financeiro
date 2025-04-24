import yfinance as yf
from datetime import datetime
from src.entities.stock_db import StockData, StockDataRepository

class StockService:
    def __init__(self):
        self.stock_repo = StockDataRepository()

    def update_stock_data(self, symbol: str) -> bool:
        """Atualiza os dados de uma ação no banco de dados"""
        try:
            # Busca dados da ação usando yfinance
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            
            if not hist.empty:
                latest_data = hist.iloc[-1]
                
                # Cria objeto StockData
                stock_data = StockData(
                    id=None,
                    symbol=symbol,
                    price=float(latest_data['Close']),
                    volume=int(latest_data['Volume']),
                    high=float(latest_data['High']),
                    low=float(latest_data['Low']),
                    open=float(latest_data['Open']),
                    close=float(latest_data['Close']),
                    date=datetime.now()
                )
                
                # Salva no banco de dados
                self.stock_repo.save_stock_data(stock_data)
                return True
            return False
            
        except Exception as e:
            print(f"Erro ao atualizar dados de {symbol}: {str(e)}")
            return False

    def get_stock_history(self, symbol: str, days: int = 30):
        """Obtém o histórico de uma ação"""
        try:
            end_date = datetime.now()
            start_date = end_date.replace(day=end_date.day - days)
            
            return self.stock_repo.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            print(f"Erro ao buscar histórico de {symbol}: {str(e)}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        """Obtém o último preço de uma ação"""
        try:
            price = self.stock_repo.get_latest_stock_price(symbol)
            return price if price is not None else 0.0
        except Exception as e:
            print(f"Erro ao buscar preço de {symbol}: {str(e)}")
            return 0.0 