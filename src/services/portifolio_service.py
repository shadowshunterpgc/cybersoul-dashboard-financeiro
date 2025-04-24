import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px

from functools import lru_cache

from src.services.dollar_service import CurrencyApi
from src.services.asset_service import AssetService

currency_api = CurrencyApi()
asset_service = AssetService()

class PortfolioService:
    def get_cotacao(self):
        try:
            # Get current quote
            current_quote = float(currency_api.get_save_currency(coin='USDBRL')['USDBRL']['bid'])
            
            # Get daily data to calculate variation
            currency_daily = currency_api.get_daily_currency()
            if currency_daily and len(currency_daily) > 1:
                # Get previous quote (second most recent)
                previous_quote = float(currency_daily[1][0])  # [1] for second item, [0] for bid value
                
                # Calculate variation
                variation = current_quote - previous_quote
                
                return current_quote, variation
            
            return current_quote, 0.00
            
        except (ValueError, TypeError, IndexError):
            return 0.00, 0.00  # Fallback em caso de erro

    def get_total_value(self) -> float:
        """Calcula o valor total do portfólio em dólares"""
        portfolio_data = asset_service.get_portfolio_data()
        if not portfolio_data:
            return 0.0
        
        total_value = 0.0
        for asset in portfolio_data:
            if 'Market Value ($)' in asset and asset['Market Value ($)']:
                try:
                    # Remove any formatting and convert to float
                    value = float(str(asset['Market Value ($)']).replace('$', '').replace(',', ''))
                    total_value += value
                except (ValueError, TypeError):
                    continue
        
        return total_value

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
            df['date_hour'] = pd.to_datetime(df['date_hour'], format='mixed')

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
        
        # Get CAIXA value
        from src.entities.caixa_db import CaixaRepository
        caixa_repo = CaixaRepository()
        caixa = caixa_repo.get_latest_caixa()
        caixa_value = float(caixa.valor) if caixa else 0.0
        
        # Calculate total value including CAIXA
        total_value_with_caixa = summary['total_value'] + caixa_value
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Valor Total", f"${total_value_with_caixa:,.2f}")
        with col2:
            st.metric("Custo Total", f"${summary['total_cost']:,.2f}")
        with col3:
            st.metric("Ganho/Perda Total", f"${summary['total_gain']:,.2f}")
        with col4:
            st.metric("Retorno Total", f"{summary['total_gain_percent']:.2f}%")
        with col5:
            st.metric("Valor do Caixa", f"${caixa_value:,.2f}")
