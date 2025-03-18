from crewai import Agent
from crewai import LLM
from crewai.project import CrewBase, agent
from src.services.dollar_service import CurrencyApi


@CrewBase
class CurrencyAgent:

    @agent
    def currency_analisys_agent(self):

        return Agent(
            role="Corretor de câmbio",
            goal="Ajuda na análise do câmbio",
            backstory="Experiência em análise e previsão do câmbio",
            system_template="""<|start_header_id|>system<|end_header_id|>
                        {{ .System }}<|eot_id|>""",
            prompt_template="""<|start_header_id|>user<|end_header_id|>
                        {{ .Prompt }}<|eot_id|>""",
            response_template="""<|start_header_id|>assistant<|end_header_id|>
                        {{ .Response }}<|eot_id|>""",
            tools=[CurrencyApi()],
            llm=LLM(model='ollama/llama3.1', api_base='http://localhost:11434'),
            max_iter=2
        )
