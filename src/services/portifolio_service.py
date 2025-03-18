import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px

from functools import lru_cache

from src.services.dollar_service import CurrencyApi

currency_api = CurrencyApi()

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
        # Lista de símbolos (tickers) do portfólio
        portfolio_symbols = ['KO', 'NKE', 'NVDA', 'BIL', 'GLD', 'JEPI', 'SGOV']

        # Dados fixos para Shares e Ac/Share (você pode torná-los dinâmicos se tiver um banco de dados)
        shares_data = {
            'KO': 0.30126924, 'NKE': 0.13761447, 'NVDA': 0.71368813,
            'BIL': 6.846257, 'GLD': 1.58998999, 'JEPI': 11.34742442, 'SGOV': 134.46761044,
        }
        ac_share_data = {
            'KO': 69.71, 'NKE': 72.67, 'NVDA': 121.13,
            'BIL': 91.66, 'GLD': 264.15, 'JEPI': 58.62, 'SGOV': 100.43
        }

        portfolio_data = []
        total_reais = 0.0
        total_cash = 0.0

        # Busca dados para cada símbolo
        for symbol in portfolio_symbols:
            stock_data = self.get_stock_data(symbol)
            if stock_data['last_price'] is None:
                continue

            # Número de ações e preço de aquisição
            shares = shares_data[symbol]
            ac_share = ac_share_data[symbol]

            # Cálculos
            last_price = stock_data['last_price']
            total_cost = shares * ac_share  # Custo total = ações * preço de aquisição
            market_value = shares * last_price  # Valor de mercado = ações * preço atual

            # Ganho/perda diário (simplificado, usando preço de fechamento do dia anterior)
            prev_close = yf.Ticker(symbol).history(period="2d")['Close'].iloc[-2] if \
            yf.Ticker(symbol).history(period="2d").shape[0] > 1 else last_price
            day_gain_unrl_dollars = market_value - (shares * prev_close)
            day_gain_unrl_percent = ((last_price - prev_close) / prev_close) * 100 if prev_close != 0 else 0

            # Ganho/perda total
            tot_gain_unrl_dollars = market_value - total_cost
            tot_gain_unrl_percent = ((last_price - ac_share) / ac_share) * 100 if ac_share != 0 else 0

            # Dados de dividendos
            dividends = stock_data['dividends']

            portfolio_data.append({
                'Symbol': symbol,
                'Status': 'Open',
                'Shares': shares,
                'Last Price': last_price,
                'Ac/Share': ac_share,
                'Total Cost ($)': total_cost,
                'Market Value ($)': market_value,
                'Tot Div': dividends,
                'Day Gain UNRL (%)': day_gain_unrl_percent,
                'Day Gain UNRL ($)': day_gain_unrl_dollars,
                'Tot Gain UNRL (%)': tot_gain_unrl_percent,
                'Tot Gain UNRL ($)': tot_gain_unrl_dollars,
                'Realized Gain (%)': 0.0,  # Isso pode ser dinâmico se você tiver histórico de transações
                'Realized Gain ($)': 0.0
            })

            # Calcula o total de cotas
            total_cash = total_cash + market_value
            total_reais = total_cash * self.get_cotacao()

        # Adiciona linha de "Total Cash" (exemplo fixo, pode ser dinâmico)

        portfolio_data.append({
            'Symbol': 'Total Cash',
            'Status': '',
            'Shares': total_cash,
            'Last Price': total_reais,
            'Ac/Share': '',
            'Total Cost ($)': '',
            'Market Value ($)': '',
            'Tot Div': '',
            'Day Gain UNRL (%)': '',
            'Day Gain UNRL ($)': '',
            'Tot Gain UNRL (%)': '',
            'Tot Gain UNRL ($)': '',
            'Realized Gain (%)': '',
            'Realized Gain ($)': ''
        })

        # Converte os dados para um DataFrame
        df = pd.DataFrame(portfolio_data)

        # Formata os números para exibição (mantendo o formato da imagem)
        numeric_columns = ['Shares', 'Last Price', 'Ac/Share', 'Total Cost ($)', 'Market Value ($)',
                           'Tot Div', 'Day Gain UNRL ($)', 'Tot Gain UNRL ($)', 'Realized Gain ($)']
        for col in numeric_columns:
            df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) and x != '' else x)

        # Formata as porcentagens (mantendo o formato da imagem)
        percentage_columns = ['Day Gain UNRL (%)', 'Tot Gain UNRL (%)', 'Realized Gain (%)']
        for col in percentage_columns:
            df[col] = df[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and x != '' else x)

        # Aplica cores condicionais (vermelho para negativo, verde para positivo)
        def color_negative_red(val):
            if pd.isna(val) or val == '':
                return ''
            try:
                # Remove formatação para verificar o valor numérico
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

        # Aplica estilo condicional ao DataFrame
        styled_df = df.style.map(color_negative_red, subset=['Day Gain UNRL (%)', 'Day Gain UNRL ($)',
                                                             'Tot Gain UNRL (%)', 'Tot Gain UNRL ($)'])

        # Exibe a tabela no Streamlit usando st.dataframe para suportar styling
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

