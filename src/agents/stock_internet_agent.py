from crewai.project import agent
from crewai import Agent, LLM, Task

from src.services.duckduckgo_service import SearchDuckDuckGoSearchApi

search_tool = SearchDuckDuckGoSearchApi()

class StockInternetAgent:

    @agent
    def stock_internet_agent(self):
        return Agent(
            role="Corretor de análise de investimentos",
            goal="Ajuda na análise de investimentos",
            backstory="Experiência em análise e previsão de investimentos",
            system_template="""<|start_header_id|>system<|end_header_id|>
                    {{ .System }}<|eot_id|>""",
            prompt_template="""<|start_header_id|>user<|end_header_id|>
                    {{ .Prompt }}<|eot_id|>""",
            response_template="""<|start_header_id|>assistant<|end_header_id|>
                    {{ .Response }}<|eot_id|>""",
            tools=[search_tool],
            llm=LLM(model='ollama/llama3.1', api_base='http://localhost:11434'),
            max_iter=2
        )

