from pydantic import BaseModel, Field, ValidationError
from decimal import Decimal
from datetime import datetime

class CurrencyQuoteModel(BaseModel):
    code: str = Field(..., min_length=1, description="Código da moeda/ação, ex.: USD")
    codein: str = Field(..., min_length=1, description="Código da moeda de conversão, ex.: BRL")
    name: str = Field(..., min_length=1, description="Nome da moeda/ação, ex.: Dólar Americano")
    high: Decimal = Field(..., ge=0, description="Preço máximo")
    low: Decimal = Field(..., ge=0, description="Preço mínimo")
    varBid: Decimal = Field(..., description="Variação do preço de compra")
    pctChange: Decimal = Field(..., ge=-100, le=100, description="Percentual de mudança (-100% a 100%)")
    bid: Decimal = Field(..., ge=0, description="Preço de compra")
    ask: Decimal = Field(..., ge=0, description="Preço de venda")
    date: datetime = Field(default_factory=datetime.now, description="Data da cotação")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # Converte datetime para string ISO no JSON
            Decimal: lambda v: str(v)  # Converte Decimal para string no JSON
        }

    def __str__(self):
        return (f"CurrencyQuoteModel(code={self.code}, codein={self.codein}, name='{self.name}', "
                f"high={self.high}, low={self.low}, varBid={self.varBid}, "
                f"pctChange={self.pctChange}, bid={self.bid}, ask={self.ask}, date={self.date})")

# Exemplo de uso
# if __name__ == "__main__":
#     try:
#         # Criar uma instância com valores de exemplo
#         quote = CurrencyQuoteModel(
#             code="USD",
#             codein="BRL",
#             name="Dólar Americano",
#             high=Decimal("5.90"),
#             low=Decimal("5.88"),
#             varBid=Decimal("0.02"),
#             pctChange=Decimal("0.34"),
#             bid=Decimal("5.89"),
#             ask=Decimal("5.90")
#         )
#         print(quote)
#         # Serializar para JSON
#         print(quote.model_dump_json())
#     except ValidationError as e:
#         print(f"Erro de validação: {e}")