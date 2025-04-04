import json
import os
from pathlib import Path
import pandas as pd
import yfinance as yf
from datetime import datetime

# Define the path for the assets database
ASSETS_DB_PATH = Path("data/db/assets.json")

class AssetService:
    """Service for managing assets in the portfolio."""
    
    def __init__(self):
        # Ensure the directory exists
        os.makedirs(os.path.dirname(ASSETS_DB_PATH), exist_ok=True)
    
    def load_assets(self):
        """Load assets from the JSON file."""
        if ASSETS_DB_PATH.exists():
            with open(ASSETS_DB_PATH, 'r') as f:
                return json.load(f)
        return []
    
    def save_assets(self, assets):
        """Save assets to the JSON file."""
        with open(ASSETS_DB_PATH, 'w') as f:
            json.dump(assets, f, indent=4)
    
    def add_asset(self, asset_data):
        """Add a new asset to the database."""
        assets = self.load_assets()
        
        # Check if asset already exists
        symbol_exists = any(asset["symbol"] == asset_data["symbol"] for asset in assets)
        
        if symbol_exists:
            return False, f"O ativo com símbolo {asset_data['symbol']} já existe."
        
        assets.append(asset_data)
        self.save_assets(assets)
        return True, f"Ativo {asset_data['symbol']} adicionado com sucesso!"
    
    def update_asset(self, symbol, asset_data):
        """Update an existing asset in the database."""
        assets = self.load_assets()
        
        # Find the asset with the given symbol
        for i, asset in enumerate(assets):
            if asset["symbol"] == symbol:
                assets[i] = asset_data
                self.save_assets(assets)
                return True, f"Ativo {symbol} atualizado com sucesso!"
        
        return False, f"Ativo com símbolo {symbol} não encontrado."
    
    def delete_asset(self, symbol):
        """Delete an asset from the database."""
        assets = self.load_assets()
        
        # Filter out the asset with the given symbol
        filtered_assets = [asset for asset in assets if asset["symbol"] != symbol]
        
        if len(filtered_assets) < len(assets):
            self.save_assets(filtered_assets)
            return True, f"Ativo {symbol} removido com sucesso!"
        
        return False, f"Ativo com símbolo {symbol} não encontrado."
    
    def clear_assets(self):
        """Clear all assets from the database."""
        self.save_assets([])
        return True, "Todos os ativos foram removidos!"
    
    def get_portfolio_data(self):
        """Get portfolio data for all assets with current market prices."""
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
                    
                    portfolio_data.append({
                        'Symbol': asset["symbol"],
                        'Name': asset["name"],
                        'Type': asset["type"],
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
                    })
            except Exception as e:
                print(f"Error fetching data for {asset['symbol']}: {e}")
        
        return portfolio_data
    
    def get_portfolio_summary(self):
        """Get a summary of the portfolio with total value and performance."""
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
        
        return {
            'total_value': df['Market Value ($)'].sum(),
            'total_cost': df['Total Cost ($)'].sum(),
            'total_gain': df['Tot Gain UNRL ($)'].sum(),
            'total_gain_percent': (df['Tot Gain UNRL ($)'].sum() / df['Total Cost ($)'].sum() * 100) if df['Total Cost ($)'].sum() > 0 else 0,
            'asset_count': len(df)
        } 