from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.model.caixa import CaixaModel

Base = declarative_base()

class Caixa(Base):
    __tablename__ = 'caixa'
    
    id = Column(Integer, primary_key=True)
    valor = Column(Numeric(10, 2), nullable=False)
    date = Column(DateTime, default=datetime.now)

class CaixaRepository:
    def __init__(self):
        # Use the same database URL as other repositories
        self.engine = create_engine('sqlite:///finance.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def save_caixa(self, caixa: CaixaModel) -> None:
        db_caixa = Caixa(
            valor=caixa.valor,
            date=caixa.date
        )
        self.session.add(db_caixa)
        self.session.commit()

    def get_latest_caixa(self) -> Optional[CaixaModel]:
        caixa = self.session.query(Caixa).order_by(Caixa.date.desc()).first()
        if caixa:
            return CaixaModel(
                id=caixa.id,
                valor=caixa.valor,
                date=caixa.date
            )
        return None

    def update_caixa(self, valor: float) -> None:
        caixa = self.session.query(Caixa).order_by(Caixa.date.desc()).first()
        if caixa:
            caixa.valor = valor
            caixa.date = datetime.now()
        else:
            new_caixa = Caixa(valor=valor)
            self.session.add(new_caixa)
        self.session.commit()

    def get_all_caixa(self) -> List[Caixa]:
        """Retorna todos os registros de caixa ordenados por data (mais recente primeiro)"""
        return self.session.query(Caixa).order_by(Caixa.date.desc()).all()

    def delete_caixa(self, caixa_id: int) -> None:
        """Deleta um registro específico de caixa pelo ID"""
        caixa = self.session.query(Caixa).filter(Caixa.id == caixa_id).first()
        if caixa:
            self.session.delete(caixa)
            self.session.commit()

    def clear_history(self) -> None:
        """Remove todos os registros de caixa"""
        self.session.query(Caixa).delete()
        self.session.commit()

    def __del__(self):
        self.session.close() 