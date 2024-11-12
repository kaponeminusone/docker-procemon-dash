from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# Definir un Enum para los roles de usuario (opcional)
class IndicatorType(str, Enum):
    type1 = 'range'
    type2 = 'checkbox'
    type3 = 'criteria'

class Indicator(BaseModel):
    id: Optional[int]
    name: str = Field(..., alias='nombre', min_length=3, max_length=50)
    type: IndicatorType = Field(default=IndicatorType.type1, alias='tipo')
    descripcion: Optional[str] = Field(None, description="Descripción opcional del Indicador")

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original

class IndicatorRead(BaseModel): #Puede que no sea necesario
    id: int
    name: str = Field(..., alias='nombre', min_length=3, max_length=50)
    type: IndicatorType = Field(default=IndicatorType.type1, alias='tipo')
    descripcion: Optional[str] = Field(None, description="Descripción opcional del Indicador")

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original

class IndicatorUpdate(BaseModel):
    id: int
    name:  Optional[str] = Field(None, alias='nombre', min_length=3, max_length=50)
    type: Optional[str] = Field(default=IndicatorType.type2, alias='tipo')

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original