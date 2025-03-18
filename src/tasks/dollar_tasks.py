from crewai import Task


class CurrencyTasks:

    def currency_task(self, agent):
        return Task(
            description="Analisa econverte um valor em reais (BRL) para dólares (USD) com base na cotação atual.",
            expected_output="O valor de R$ 100,00 equivale a aproximadamente US$ 18,18 (cotação: 5,50).",
            agent=agent
        )