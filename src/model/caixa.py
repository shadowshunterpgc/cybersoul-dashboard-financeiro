from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

class CaixaModel(BaseModel):
    id: int | None = Field(default=None, description="ID do registro")
    valor: Decimal = Field(..., ge=0, description="Valor total do caixa")
    date: datetime = Field(default_factory=datetime.now, description="Data do registro")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }

    def __str__(self):
        return f"CaixaModel(id={self.id}, valor={self.valor}, date={self.date})" 