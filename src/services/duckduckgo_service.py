import time

from abc import ABC
from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun


class SearchDuckDuckGoSearchApi(BaseTool, ABC):
    name: str = "SearchDuckDuckGoSearchApi"
    description: str = "Busca informações da internet."
    search_tool: DuckDuckGoSearchRun = None  # Define search_tool como um atributo da classe

    def __init__(self, **data):
        super().__init__(**data)
        # Inicializa a ferramenta de busca do DuckDuckGo
        self.search_tool = DuckDuckGoSearchRun()

    def _run(self, query: str) -> str:
        try:
            time.sleep(2)  # Adiciona um delay entre as requisições
            results = self.search_tool.run(query)
            return self.process_results(results)
        except Exception as e:
            return f"Erro ao buscar por: {query} - Mensagem de erro: {e}"

    def process_results(self, results: str) -> str:
        # Exemplo de processamento de resultados
        # Aqui você pode filtrar, ordenar ou extrair informações específicas dos resultados
        return f"Resultados da busca: {results}"


