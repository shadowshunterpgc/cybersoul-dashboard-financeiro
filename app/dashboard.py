import time

import streamlit as st

from crewai import Crew, Process

from src.agents.dollar_agent import CurrencyAgent
from src.agents.stock_internet_agent import StockInternetAgent
from src.tasks.dollar_tasks import CurrencyTasks
from src.tasks.post_task import PostTasks
from src.tasks.stock_internet_task import StockInternetTask
from src.services.portifolio_service import PortfolioService
from app.settings import settings_page


portifolio = PortfolioService()


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


def get_dados_financeiros():
    stock_agent = StockInternetAgent()
    stock_tasks = StockInternetTask()

    agent_stock_instance = stock_agent.stock_internet_agent()
    task_stock_instance = stock_tasks.stock_internet_task(agent=agent_stock_instance, symbols=['NVDA', 'PTEN', 'SPY', 'GLD', 'JEPI'])

    crew = Crew(
        agents=[agent_stock_instance],
        tasks=[task_stock_instance],
        process=Process.sequential,
        verbose=True
    )
    result = stream_data(str(crew.kickoff()))
    st.write_stream(result)


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
    task = stock_agent.create_cache_analysis_task(symbols=["KO", "NKE", "NVDA", "BIL", "GLD", "JEPI"])  # Use os mesmos símbolos do portfólio

    crew = Crew(
        agents=[stock_agent.cache_analyzer_agent()],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    try:
        # Executa o Crew para obter as dicas
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
        st.session_state["cotacao"] = f"R${portifolio.get_cotacao():.4f}"
        st.session_state["dolar_metrica"] = portifolio.dolar_metrica()
        st.session_state["portfolio"] = portifolio.portfolio()
        st.session_state["dados_financeiros"] = get_dados_financeiros()

        time.sleep(60)
        st.rerun()  # Recarrega a página para exibir novos dados


def tabs():
    financeiro, configuracoes = st.tabs(['Financeiro', 'Configurações'])

    with financeiro:
        st.metric('Cotação do Dólar', st.session_state.get('cotacao'))
        st.session_state.get('dolar_metrica')
        st.session_state.get('portifolio')
        st.session_state.get('dados_financeiros')
    
    with configuracoes:
        settings_page()


if __name__ == '__main__':
    print(st.session_state.get('cotacao'))
    logo()
    tabs()
    atualizar_dados()

