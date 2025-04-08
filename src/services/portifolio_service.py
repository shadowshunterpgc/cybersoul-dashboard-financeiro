import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import json
import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal

from functools import lru_cache

from src.services.dollar_service import CurrencyApi
from src.entities.assets_db import (
    save_asset, update_asset, delete_asset, get_asset_by_symbol, 
    get_all_assets, save_asset_history, save_portfolio_history
)
from src.model.asset_model import AssetModel, AssetHistoryModel, PortfolioHistoryModel

currency_api = CurrencyApi()

# Define the path for the assets database (keeping JSON for compatibility)
ASSETS_DB_PATH = Path("data/db/assets.json")

class AssetService:
    """Service for managing assets in the portfolio."""
    
    def __init__(self):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(ASSETS_DB_PATH), exist_ok=True)
    
    def load_assets(self):
        """Load assets from the database or JSON file."""
        # Try to get assets from the database first
        db_assets = get_all_assets()
        
        if db_assets:
            # Convert from DB model to dictionary
            return [
                {
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "type": asset.type,
                    "shares": float(asset.shares),
                    "purchase_price": float(asset.purchase_price),
                    "purchase_date": asset.purchase_date,
                    "notes": asset.notes or ""
                }
                for asset in db_assets
            ]
        
        # Fall back to JSON if no database assets
        if ASSETS_DB_PATH.exists():
            with open(ASSETS_DB_PATH, 'r') as f:
                assets = json.load(f)
                
                # If we have JSON assets but not DB assets, migrate them
                if assets:
                    for asset_data in assets:
                        self._save_to_db(asset_data)
                
                return assets
        
        return []
    
    def _save_to_db(self, asset_data):
        """Internal method to save an asset to the database."""
        asset_model = AssetModel(
            symbol=asset_data["symbol"],
            name=asset_data["name"],
            type=asset_data.get("type", "Ação"),
            shares=Decimal(str(asset_data["shares"])),
            purchase_price=Decimal(str(asset_data["purchase_price"])),
            purchase_date=asset_data["purchase_date"],
            notes=asset_data.get("notes", "")
        )
        return save_asset(asset_model)
    
    def save_assets(self, assets):
        """Save assets to both JSON and database."""
        # Save to JSON for backward compatibility
        with open(ASSETS_DB_PATH, 'w') as f:
            json.dump(assets, f, indent=4)
    
    def add_asset(self, asset_data):
        """Add a new asset to the database."""
        # Check if asset already exists in the database
        existing_asset = get_asset_by_symbol(asset_data["symbol"])
        if existing_asset:
            return False, f"O ativo com símbolo {asset_data['symbol']} já existe."
        
        # Save to JSON file for backward compatibility
        assets = self.load_assets()
        symbol_exists = any(asset["symbol"] == asset_data["symbol"] for asset in assets)
        if not symbol_exists:
            assets.append(asset_data)
            self.save_assets(assets)
        
        # Save to SQLite database
        asset_id = self._save_to_db(asset_data)
        
        if asset_id:
            return True, f"Ativo {asset_data['symbol']} adicionado com sucesso!"
        else:
            return False, f"Erro ao adicionar ativo {asset_data['symbol']} no banco de dados."
    
    def update_asset(self, symbol, asset_data):
        """Update an existing asset in the database."""
        # Check if asset exists in the database
        existing_asset = get_asset_by_symbol(symbol)
        
        # Update JSON file for backward compatibility
        assets = self.load_assets()
        for i, asset in enumerate(assets):
            if asset["symbol"] == symbol:
                assets[i] = asset_data
                self.save_assets(assets)
                break
        
        # Update or insert into SQLite database
        if existing_asset:
            # Update existing record
            asset_model = AssetModel(
                symbol=asset_data["symbol"],
                name=asset_data["name"],
                type=asset_data.get("type", "Ação"),
                shares=Decimal(str(asset_data["shares"])),
                purchase_price=Decimal(str(asset_data["purchase_price"])),
                purchase_date=asset_data["purchase_date"],
                notes=asset_data.get("notes", "")
            )
            
            if update_asset(existing_asset.id, asset_model):
                return True, f"Ativo {symbol} atualizado com sucesso!"
            else:
                return False, f"Erro ao atualizar ativo {symbol} no banco de dados."
        else:
            # Insert new record
            return self.add_asset(asset_data)
    
    def delete_asset(self, symbol):
        """Delete an asset from the database."""
        # Check if asset exists in the database
        existing_asset = get_asset_by_symbol(symbol)
        
        # Delete from JSON file for backward compatibility
        assets = self.load_assets()
        filtered_assets = [asset for asset in assets if asset["symbol"] != symbol]
        if len(filtered_assets) < len(assets):
            self.save_assets(filtered_assets)
        
        # Delete from SQLite database if exists
        if existing_asset and delete_asset(existing_asset.id):
            return True, f"Ativo {symbol} removido com sucesso!"
        else:
            # If we deleted from JSON but not from DB (or it didn't exist in DB)
            if len(filtered_assets) < len(assets):
                return True, f"Ativo {symbol} removido com sucesso!"
            return False, f"Ativo com símbolo {symbol} não encontrado."
    
    def clear_assets(self):
        """Clear all assets from both JSON and database."""
        # Clear JSON file
        self.save_assets([])
        
        # Clear SQLite database - delete all assets
        assets = get_all_assets()
        for asset in assets:
            delete_asset(asset.id)
        
        return True, "Todos os ativos foram removidos!"
    
    def get_portfolio_data(self):
        """Get portfolio data for all assets with current market prices and store historical data."""
        assets = self.load_assets()
        portfolio_data = []
        
        for asset in assets:
            try:
                # Get current market data
                ticker = yf.Ticker(asset["symbol"])
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    last_price = hist['Close'].iloc[-1]
                    
                    # Calculate values
                    shares = asset["shares"]
                    purchase_price = asset["purchase_price"]
                    total_cost = shares * purchase_price
                    market_value = shares * last_price
                    
                    # Calculate gains/losses
                    day_change = ((last_price - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100 if hist['Open'].iloc[0] != 0 else 0
                    total_gain_percent = ((last_price - purchase_price) / purchase_price) * 100 if purchase_price != 0 else 0
                    total_gain_dollars = market_value - total_cost
                    
                    # Get dividends if available
                    dividends = ticker.dividends.tail(1).sum() if not ticker.dividends.empty else 0.0
                    
                    # Create portfolio data entry
                    entry = {
                        'Symbol': asset["symbol"],
                        'Name': asset["name"],
                        'Type': asset.get("type", "Ação"),
                        'Shares': shares,
                        'Last Price': last_price,
                        'Ac/Share': purchase_price,
                        'Total Cost ($)': total_cost,
                        'Market Value ($)': market_value,
                        'Tot Div': dividends,
                        'Day Gain UNRL (%)': day_change,
                        'Day Gain UNRL ($)': shares * (last_price - hist['Open'].iloc[0]),
                        'Tot Gain UNRL (%)': total_gain_percent,
                        'Tot Gain UNRL ($)': total_gain_dollars,
                        'Purchase Date': asset["purchase_date"],
                        'Notes': asset.get("notes", "")
                    }
                    
                    portfolio_data.append(entry)
                    
                    # Save historical data to SQLite
                    db_asset = get_asset_by_symbol(asset["symbol"])
                    if db_asset:
                        # Save asset history
                        history = AssetHistoryModel(
                            asset_id=db_asset.id,
                            date_checked=datetime.now(),
                            price=Decimal(str(last_price)),
                            market_value=Decimal(str(market_value)),
                            day_gain_percent=Decimal(str(day_change)),
                            day_gain_dollars=Decimal(str(shares * (last_price - hist['Open'].iloc[0]))),
                            total_gain_percent=Decimal(str(total_gain_percent)),
                            total_gain_dollars=Decimal(str(total_gain_dollars)),
                            dividends=Decimal(str(dividends))
                        )
                        save_asset_history(history)
            except Exception as e:
                print(f"Error fetching data for {asset['symbol']}: {e}")
        
        return portfolio_data
    
    def get_portfolio_summary(self):
        """Get a summary of the portfolio with total value and performance and store historical data."""
        portfolio_data = self.get_portfolio_data()
        
        if not portfolio_data:
            return {
                'total_value': 0,
                'total_cost': 0,
                'total_gain': 0,
                'total_gain_percent': 0,
                'asset_count': 0
            }
        
        df = pd.DataFrame(portfolio_data)
        
        summary = {
            'total_value': df['Market Value ($)'].sum(),
            'total_cost': df['Total Cost ($)'].sum(),
            'total_gain': df['Tot Gain UNRL ($)'].sum(),
            'total_gain_percent': (df['Tot Gain UNRL ($)'].sum() / df['Total Cost ($)'].sum() * 100) if df['Total Cost ($)'].sum() > 0 else 0,
            'asset_count': len(df)
        }
        
        # Save portfolio history to SQLite
        history = PortfolioHistoryModel(
            date_checked=datetime.now(),
            total_value=Decimal(str(summary['total_value'])),
            total_cost=Decimal(str(summary['total_cost'])),
            total_gain=Decimal(str(summary['total_gain'])),
            total_gain_percent=Decimal(str(summary['total_gain_percent'])),
            asset_count=summary['asset_count']
        )
        save_portfolio_history(history)
        
        return summary


class PortfolioService:
    def get_cotacao(self):
        try:
            return float(currency_api.get_save_currency(coin='USDBRL')['USDBRL']['bid'])
        except (ValueError, TypeError):
            return 0.00  # Fallback em caso de erro

    def dolar_metrica(self):
        """Exibe os dados diários da cotação do dólar em um gráfico de linha com botões de zoom no Streamlit."""
        # Obtém os dados diários
        currency_daily = currency_api.get_daily_currency()

        if currency_daily:
            # Converte a lista de tuplas para DataFrame, especificando as colunas
            df = pd.DataFrame(currency_daily, columns=['bid', 'date_hour'])

            # Converte 'bid' para float (ou Decimal, se preferir precisão)
            df['bid'] = df['bid'].apply(lambda x: float(x) if pd.notna(x) else 0.0)

            # Filtra os valores onde 'bid' não é 0
            df = df[df['bid'] != 0.0]

            # Converte 'date_hour' para datetime para o eixo X
            df['date_hour'] = pd.to_datetime(df['date_hour'])

            # Ordena por 'date_hour' para manter a ordem cronológica (do mais antigo para o mais recente)
            df = df.sort_values('date_hour', ascending=True)

            with st.expander("Variação do Dólar/Real"):
                # Verifica se há dados após o filtro
                if not df.empty:
                    # Filtrar os dados das últimas 4 horas
                    df_recente = df[df['date_hour'] > pd.Timestamp.now() - pd.Timedelta(hours=1)]

                    # Exibe o gráfico de linha com botões de zoom
                    fig = px.line(df_recente, x='date_hour', y='bid',
                                  labels={'bid': 'Cotação', 'date_hour': 'Data/Hora'})

                    st.plotly_chart(fig, use_container_width=True, width=100, height=100)
                else:
                    st.warning("Nenhum dado válido disponível para a cotação após filtrar valores zero.")
        else:
            st.warning("Nenhum dado diário disponível para a cotação.")


    @lru_cache(maxsize=128)  # Adiciona caching para evitar chamadas repetidas
    def get_stock_data(self, symbol):
        """Busca dados de uma ação específica do Yahoo Finance com caching."""
        try:
            stock = yf.Ticker(symbol)
            # Usa dados diários em vez de minuto a minuto para maior velocidade
            hist = stock.history(period="1d")
            last_price = hist['Close'].iloc[-1] if not hist.empty else stock.fast_info['lastPrice']
            dividends = stock.dividends.tail(1).sum() if not stock.dividends.empty else 0.0
            return {
                'last_price': last_price,
                'dividends': dividends
            }
        except Exception as e:
            st.error(f"Erro ao buscar dados para {symbol}: {e}")
            return {'last_price': None, 'dividends': 0.0}


    def portfolio(self):
        """Exibe uma tabela de portfólio financeiro dinâmica com dados otimizados do Yahoo Finance, mantendo cores (vermelho para negativo, verde para positivo) no componente padrão do Streamlit."""
        # Get portfolio data from the asset service
        portfolio_data = asset_service.get_portfolio_data()
        
        if not portfolio_data:
            st.info("Nenhum ativo cadastrado. Adicione ativos na aba de Configurações.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(portfolio_data)
        
        # Format numeric columns
        numeric_columns = ['Shares', 'Last Price', 'Ac/Share', 'Total Cost ($)', 'Market Value ($)',
                           'Tot Div', 'Day Gain UNRL ($)', 'Tot Gain UNRL ($)']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) and x != '' else x)

        # Format percentage columns
        percentage_columns = ['Day Gain UNRL (%)', 'Tot Gain UNRL (%)']
        for col in percentage_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and x != '' else x)

        # Apply conditional styling
        def color_negative_red(val):
            if pd.isna(val) or val == '':
                return ''
            try:
                # Remove formatting to check numeric value
                if isinstance(val, str):
                    if '%' in val:
                        num = float(val.replace('%', ''))
                    elif '$' in val or ',' in val:
                        num = float(val.replace('$', '').replace(',', ''))
                    else:
                        num = float(val)
                else:
                    num = float(val)
                color = 'red' if num < 0 else 'green' if num > 0 else ''
                return f'color: {color}'
            except (ValueError, TypeError):
                return ''

        # Apply conditional styling to DataFrame
        styled_df = df.style.map(color_negative_red, subset=['Day Gain UNRL (%)', 'Day Gain UNRL ($)',
                                                             'Tot Gain UNRL (%)', 'Tot Gain UNRL ($)'])

        # Display the table in Streamlit
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Display portfolio summary
        summary = asset_service.get_portfolio_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Valor Total", f"${summary['total_value']:,.2f}")
        with col2:
            st.metric("Custo Total", f"${summary['total_cost']:,.2f}")
        with col3:
            st.metric("Ganho/Perda Total", f"${summary['total_gain']:,.2f}")
        with col4:
            st.metric("Retorno Total", f"{summary['total_gain_percent']:.2f}%")

