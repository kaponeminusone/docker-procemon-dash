from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# Definir un Enum para los roles de usuario (opcional)
class InputType(str, Enum):
    type1 = "int"
    type2 = "float"

class Input(BaseModel):
    id: Optional[int]
    name: str = Field(..., alias='nombre', min_length=3, max_length=50)
    type: InputType = Field(default=InputType.type1, alias='tipo')
    descripcion: Optional[str] = Field(None, description="Descripción opcional del Entrada/Salida")

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original

class InputRead(BaseModel): #Puede que no sea necesario
    id: int
    name: str = Field(..., alias='nombre', min_length=3, max_length=50)
    type: InputType = Field(default=InputType.type1, alias='tipo')
    descripcion: Optional[str] = Field(None, description="Descripción opcional del Entrada/Salida")

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original

class InputUpdate(BaseModel):
    id: int
    name:  Optional[str] = Field(None, alias='nombre', min_length=3, max_length=50)
    type: Optional[str] = Field(default=InputType.type2, alias='tipo')

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original