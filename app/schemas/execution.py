from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

from typing import List, Optional
from pydantic import BaseModel

# Definir los esquemas de entrada, salida, e indicadores

class EntradaSchema(BaseModel):
    id: int
    value: float

class IndicadorSchema(BaseModel):
    id: int
    entrada_id: int
    checkbox: Optional[bool] = None  # Campo opcional
    range: Optional[str] = None  # Opcional dependiendo del indicador
    criteria: Optional[str] = None  # Criterio alternativo
    state: Optional[bool] = None     # Nuevo campo para indicar si afecta o no

class SalidaSchema(BaseModel):
    id: int
    value: float

class EtapaSchema(BaseModel):
    num_etapa: int
    entradas: List[EntradaSchema]
    indicadores: List[IndicadorSchema]
    salidas: List[SalidaSchema]

class EjecucionProcesoSchema(BaseModel):
    id_proceso: int
    etapas: List[EtapaSchema]


# Schema para guardar en JSON
class EtapaRegistroSchema(BaseModel):
    num_etapa: int
    conformes: int
    no_conformes: int
    state: bool
    entradas: List[EntradaSchema]
    indicadores: List[IndicadorSchema]
    salidas: List[SalidaSchema]

class RegistroEjecucionSchema(BaseModel):
    id_proceso_ejecutado: int
    id_proceso: int
    no_conformes: int
    conformes: int
    num_etapas: int
    etapas: List[EtapaRegistroSchema]


class MaterialSchema(BaseModel):
    id: int  # ID del material (id_entrada en tu base de datos)
    value: float  # Valor que se sumará a cantidad_entrada

class ProcesoEjecutadoSchema(BaseModel):
    id_proceso: int
    id_proceso_ejecutado: int
    num_etapas_con_conformidades: int
    tasa_de_exito: float
    no_conformidades: int
    conformidades: int

    class Config:
        from_attributes = True  # Permite trabajar con objetos ORM