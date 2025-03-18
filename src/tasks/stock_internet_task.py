import datetime

from crewai import Task
from datetime import datetime


class StockInternetTask:

    def stock_internet_task(self, agent, symbol):
        current_date = datetime.now().strftime('%d/%m/%Y')
        return Task(
            description="Analyze current market conditions and major indices.",
            expected_output=f"Provide a market summary in {current_date} for {symbol} and compare with other options.",
            agent=agent
        )

    # Opcional: Adicione uma tarefa para usar o novo agente
    def create_cache_analysis_task(self, symbols, agent):
        """
        Cria uma tarefa para o cache_analyzer_agent analisar os dados cached e fornecer dicas.
        """
        return Task(
            description=f"Analise os dados cached para os símbolos {symbols} e forneça 3 dicas de investimento com base em desempenho, ganhos/perdas diárias e totais, e dividendos.",
            expected_output="Uma lista de 3 dicas de investimento claras e acionáveis, formatadas em texto simples.",
            agent=agent
        )