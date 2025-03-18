import json
import logging
from datetime import datetime
from decimal import Decimal

import requests

from abc import ABC
from crewai.tools import BaseTool

from src.model.currency import CurrencyQuoteModel
from src.entities.dollar_db import init_db
from src.entities.dollar_db import save_dollar, get_daily_dollar

class CurrencyApi(BaseTool, ABC):
    name: str = "CurrencyApi()"
    func: str = "_run"
    description: str = "Busca informações sobre a cotação do dólar ou outras moedas usando a AwesomeAPI."


    def _run(self) -> float:
        global moeda
        try:
            moeda = 'USDBRL'
            cotacao = self.get_currency(coin=moeda)
            moeda_key = f"{moeda[0:3]}{moeda[3:6]}"  # Ex: 'USDBRL'
            bid = cotacao[moeda_key]['bid']
            logging.debug(f"Moeda {moeda} cotação: {bid}")
            return bid
        except Exception as e:
            logging.error(f"Erro ao obter a cotação da moeda {moeda}: {e}")
            return None


    def get_currency(self, coin: str):
        url = f'https://economia.awesomeapi.com.br/json/last/{coin[0:3]}-{coin[3:6]}'
        response = requests.get(url).content
        currency = json.loads(response)
        return currency


    def get_save_currency(self, coin: str):
        url = f'https://economia.awesomeapi.com.br/json/last/{coin[0:3]}-{coin[3:6]}'
        response = requests.get(url).content
        currency_json = json.loads(response)
        currency = self.put_currency(currency_json)
        return currency

    def get_daily_currency(self):
        init_db()
        return get_daily_dollar()

    def put_currency(self, cotacao):
        currency = cotacao
        quote_data = {
            "code": currency['USDBRL']['code'],
            "codein": currency['USDBRL']['codein'],
            "name": currency['USDBRL']['name'],
            "high": Decimal(str(currency['USDBRL']['high'])),
            "low": Decimal(str(currency['USDBRL']['low'])),
            "varBid": Decimal(str(currency['USDBRL']['varBid'])),
            "pctChange": Decimal(str(currency['USDBRL']['pctChange'])),
            "bid": Decimal(str(currency['USDBRL']['bid'])),
            "ask": Decimal(str(currency['USDBRL']['ask'])),
            "date": datetime.now()
        }
        quote = CurrencyQuoteModel(**quote_data)
        init_db()
        save_dollar(quote)  # Chama a função save_dollar com o modelo
        return cotacao


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging (se necessário)
    logging.basicConfig(level=logging.DEBUG)

    currency_tool = CurrencyApi()
    response = currency_tool.get_currency(coin='USDBRL')

    # Ou usar o método save_dollar para criar e salvar a instância
    quote = currency_tool.put_currency()
    print(quote)

    # Serializar para JSON
    json_data = quote.model_dump_json()
    print("JSON:", json_data)