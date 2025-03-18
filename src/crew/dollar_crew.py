from crewai import Crew, Process

from src.agents.dollar_agent import CurrencyAgent
from src.tasks.dollar_tasks import CurrencyTasks

currency_agent = CurrencyAgent()
currency_task = CurrencyTasks()

class CurrencyCrew:

    def currency_crew(self) -> Crew:
        crew =  Crew(
            agents=[currency_agent.currency_analisys_agent()],
            tasks=[currency_task.currency_task(agent=currency_agent.currency_analisys_agent())],
            process=Process.sequential,
            verbose=True
        )
        return crew