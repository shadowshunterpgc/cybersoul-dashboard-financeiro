from crewai import Agent, LLM
from crewai.project import agent

from src.services.selenium_service import SeleniumPostAgent

selenium_post_agent = SeleniumPostAgent()

class PostAgents:

    @agent
    def post_blogger_agent(self):
        return Agent(
            role="Blogger",
            goal="Escreve um post para o blogger",
            backstory="Experiência em escrever posts para o blogger",
            system_template="""<|start_header_id|>system<|end_header_id|>
                    {{ .System }}<|eot_id|>""",
            prompt_template="""<|start_header_id|>user<|end_header_id|>
                    {{ .Prompt }}<|eot_id|>""",
            response_template="""<|start_header_id|>assistant<|end_header_id|>
                    {{ .Response }}<|eot_id|>""",
            llm=LLM(model='ollama/llama3.2', api_base='http://localhost:11434'),
            max_iter=2
        )

    @agent
    def post_linkedin_agent(self):
        return Agent(
            role="Blogger",
            goal="Escreve um post para o blogger",
            backstory="Experiência em escrever posts para o blogger",
            system_template="""<|start_header_id|>system<|end_header_id|>
                    {{ .System }}<|eot_id|>""",
            prompt_template="""<|start_header_id|>user<|end_header_id|>
                    {{ .Prompt }}<|eot_id|>""",
            response_template="""<|start_header_id|>assistant<|end_header_id|>
                    {{ .Response }}<|eot_id|>""",
            tools=[selenium_post_agent],  # criar uma instância da classe
            llm=LLM(model='ollama/llama3.2', api_base='http://localhost:11434'),
            max_iter=2
        )