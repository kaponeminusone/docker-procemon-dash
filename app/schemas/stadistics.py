from typing import List, Optional
from pydantic import BaseModel

# Schema para la estadística de estado de entradas y salidas
class MaterialEntradaSalidaSchema(BaseModel):
    id: int
    nombre: str
    cantidad_entrada: float
    cantidad_salida: float
    usos: int

# Schema para el diagrama de no conformidades (general)
class DiagramaNoConformidadesSchema(BaseModel):
    conformes: int
    no_conformes: int

# Schema para el estado general por etapas
class EstadoEtapasSchema(BaseModel):
    num_etapa: int
    conformes: int
    no_conformes: int

# Schema para la estadística de procesos con éxito
class ProcesoExitoSchema(BaseModel):
    id_proceso: int
    nombre: str
    exito_promedio: float

# Schema principal para la respuesta de estadísticas
class EstadisticasResponseSchema(BaseModel):
    estado_entradas_salidas: List[MaterialEntradaSalidaSchema]
    diagrama_no_conformidades: DiagramaNoConformidadesSchema
    estado_general_etapas: List[EstadoEtapasSchema]
    procesos_menos_exito: List[ProcesoExitoSchema]
    procesos_mayor_exito: List[ProcesoExitoSchema]
