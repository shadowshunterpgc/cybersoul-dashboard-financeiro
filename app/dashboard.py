import time
from datetime import datetime

import streamlit as st
import yfinance as yf

from crewai import Crew, Process

from src.agents.dollar_agent import CurrencyAgent
from src.agents.stock_internet_agent import StockInternetAgent
from src.tasks.dollar_tasks import CurrencyTasks
from src.tasks.post_task import PostTasks
from src.tasks.stock_internet_task import StockInternetTask
from src.services.portifolio_service import PortfolioService
from src.services.asset_service import AssetService
from src.services.stock_service import StockService
from src.entities.stock_db import StockData, StockDataRepository
from src.entities.caixa_db import CaixaRepository
from app.settings import settings_page


portifolio = PortfolioService()
stock_service = StockService()
caixa_repo = CaixaRepository()


# Função para buscar a cotação inicial
def logo():
    st.set_page_config(page_title='{ cybersoul }', layout="wide")
    st.logo('app/images/logotipo_flat_branco.png', size='large')


def get_analise_cotacao():
    currency_agent = CurrencyAgent()
    currency_tasks = CurrencyTasks()

    agent_analisys_instance = currency_agent.currency_analisys_agent()
    task_analisys_instance = currency_tasks.currency_task(agent=agent_analisys_instance)

    crew = Crew(
        agents=[agent_analisys_instance],
        tasks=[task_analisys_instance],
        process=Process.sequential,
        verbose=True
    )
    st.write_stream(stream_data(str(crew.kickoff())))


def get_symbols_from_database():
    """Obtém a lista de símbolos cadastrados na base de dados"""
    asset_service = AssetService()
    assets = asset_service.load_assets()
    return [asset["symbol"] for asset in assets] if assets else []


def get_dados_financeiros():
    stock_agent = StockInternetAgent()
    stock_tasks = StockInternetTask()

    # Obter símbolos dinamicamente da base
    symbols = get_symbols_from_database()
    
    if not symbols:
        st.warning("Nenhum ativo cadastrado. Adicione ativos na aba de Configurações.")
        return

    agent_stock_instance = stock_agent.stock_internet_agent()
    task_stock_instance = stock_tasks.stock_internet_task(agent=agent_stock_instance, symbols=symbols)

    crew = Crew(
        agents=[agent_stock_instance],
        tasks=[task_stock_instance],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    
    # Save the stock data to database
    try:
        progress_bar = st.progress(0)
        for idx, symbol in enumerate(symbols):
            try:
                # Atualiza dados da ação no banco de dados
                if stock_service.update_stock_data(symbol):
                    st.success(f"✅ Dados de {symbol} atualizados com sucesso")
                else:
                    st.warning(f"⚠️ Sem dados disponíveis para {symbol}")
            except Exception as e:
                st.error(f"❌ Erro ao processar {symbol}: {str(e)}")
                continue
            finally:
                # Atualizar barra de progresso
                progress_bar.progress((idx + 1) / len(symbols))

    except Exception as e:
        st.error(f"Erro ao salvar dados: {str(e)}")
        st.error(f"Detalhes do erro: {type(e).__name__}")
    
    # Converter resultado para string para streaming
    result_str = str(result) if not isinstance(result, str) else result
    st.write_stream(stream_data(result_str))

    # Get all data for a symbol
    data = stock_repo.get_stock_data("AAPL")

    # Get data for a date range
    data = stock_repo.get_stock_data(
        "AAPL",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 3, 1)
    )

    # Get latest price
    price = stock_repo.get_latest_stock_price("AAPL")

    stock_data = StockData(
        id=None,
        symbol="AAPL",
        price=150.25,
        volume=1000000,
        high=151.00,
        low=149.50,
        open=149.75,
        close=150.25,
        date=datetime.now()
    )
    stock_repo.save_stock_data(stock_data)


def get_post_linkedin():
    post_agent = PostAgents()
    post_tasks = PostTasks()

    post_agent_instance = post_agent.post_linkedin_agent(),
    post_task_instance = post_tasks.post_linkedin_task(post_agent_instance),

    crew = Crew(
        agents=[post_agent_instance],
        tasks=[post_task_instance],
        process=Process.sequential,
        verbose=True
    )
    result = stream_data(str(crew.kickoff()))
    st.write_stream(result)


def get_investment_tips():
    """Obtém dicas de investimento usando o cache_analyzer_agent com base nos dados cached."""
    stock_agent = StockInternetAgent()

    # Obter símbolos dinamicamente da base
    symbols = get_symbols_from_database()

    if not symbols:
        st.warning("Nenhum ativo cadastrado. Adicione ativos na aba de Configurações.")
        return

    task = stock_agent.create_cache_analysis_task(symbols=symbols)

    crew = Crew(
        agents=[stock_agent.cache_analyzer_agent()],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    try:
        result = crew.kickoff()
        st.write("Dicas de Investimento:")
        st.write(result)
    except Exception as e:
        st.error(f"Erro ao gerar dicas de investimento: {e}")

def stream_data(cotacao):
    for word in cotacao.split(" "):
        frases = " " + word + " "
        yield frases
        time.sleep(0.02)


def atualizar_dados():
    """Atualiza os dados periodicamente sem usar threads."""
    while True:
        # Atualiza cotação do dólar
        cotacao, variacao = portifolio.get_cotacao()
        st.session_state["cotacao"] = f"R${cotacao:.4f}"
        st.session_state["variacao_dolar"] = f"{variacao:.2f}"
        st.session_state["dolar_metrica"] = portifolio.dolar_metrica()
        
        # Atualiza dados das ações
        symbols = get_symbols_from_database()
        if symbols:
            for symbol in symbols:
                try:
                    stock_service.update_stock_data(symbol)
                except Exception as e:
                    print(f"Erro ao atualizar {symbol}: {str(e)}")
        
        # Atualiza portfólio
        st.session_state["portfolio"] = portifolio.portfolio()
        
        # Get latest CAIXA value
        caixa = caixa_repo.get_latest_caixa()
        if caixa:
            st.session_state["caixa"] = f"${float(caixa.valor):,.2f}"
        else:
            st.session_state["caixa"] = "$0.00"
        
        # Calculate total value including CAIXA
        total_value = portifolio.get_total_value()
        if caixa:
            total_value += float(caixa.valor)
        st.session_state["total_value"] = f"${total_value:,.2f}"

        time.sleep(3)
        st.rerun(scope="app")


def tabs():
    financeiro, configuracoes = st.tabs(['Financeiro', 'Configurações'])

    with financeiro:
        col1, col2, col3 = st.columns(3)

        with col1:
            # Cotação do Dólar
            st.metric(
                'Cotação do Dólar',
                st.session_state.get('cotacao'),
                delta=st.session_state.get('variacao_dolar', 0.00)
            )

        with col2:
            # Valor do Caixa
            st.metric(
                'Valor do Caixa',
                st.session_state.get('caixa', '$0.00'),
                delta=None
            )

        with col3:
            # Valor Total (incluindo Caixa)
            st.metric(
                'Valor Total',
                st.session_state.get('total_value', '$0.00'),
                delta=None
            )

        # Métricas do dólar
        if isinstance(st.session_state.get('dolar_metrica'), dict):
            st.write(st.session_state.get('dolar_metrica'))

        # Portfolio
        if isinstance(st.session_state.get('portfolio'), dict):
            st.write(st.session_state.get('portfolio'))

        # Dados financeiros
        if st.session_state.get('dados_financeiros'):
            st.write(st.session_state.get('dados_financeiros'))

    with configuracoes:
        settings_page()


def initialize_default_values():
    """Initialize default values in the session state if they don't exist"""
    if "cotacao" not in st.session_state:
        st.session_state["cotacao"] = "Carregando..."
    if "caixa" not in st.session_state:
        st.session_state["caixa"] = "$0.00"
    if "total_value" not in st.session_state:
        st.session_state["total_value"] = "$0.00"


if __name__ == '__main__':
    initialize_default_values()
    logo()
    tabs()
    atualizar_dados()

