import yfinance as yf
from abc import ABC
from crewai.tools import BaseTool
from datetime import datetime, timedelta
import pandas as pd

class SearchDuckDuckGoSearchApi(BaseTool, ABC):
    name: str = "SearchDuckDuckGoSearchApi"
    description: str = "Busca informações do mercado financeiro usando Yahoo Finance."

    def _run(self, query: str) -> str:
        try:
            # Get market data for major indices
            indices = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                '^BVSP': 'IBOVESPA'
            }
            
            results = []
            for symbol, name in indices.items():
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    last_price = info['Close'].iloc[-1]
                    change = ((last_price - info['Open'].iloc[0]) / info['Open'].iloc[0]) * 100
                    results.append(f"{name}: {last_price:.2f} ({change:+.2f}%)")

            # Get top gainers and losers
            sp500 = yf.Ticker('^GSPC')
            sp500_components = pd.DataFrame()
            try:
                sp500_components = sp500.history(period='2d')
            except:
                pass

            market_summary = "\n".join(results)
            current_date = datetime.now().strftime('%d/%m/%Y')
            
            return f"""Análise de Mercado - {current_date}

Índices Principais:
{market_summary}

Observação: Dados fornecidos pelo Yahoo Finance em tempo real.
Para análises mais detalhadas, recomenda-se consultar diretamente plataformas financeiras especializadas."""

        except Exception as e:
            return f"Erro ao buscar dados do mercado: {str(e)}"


