from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

from app.schemas.user import UserRead

class RegistroRead(BaseModel):
    id: int
    id_usuario: int
    descripcion: Optional[str] = None
    creado: datetime
    modificado: datetime
    id_proceso: Optional[int] = None
    id_indicador: Optional[int] = None
    id_entrada: Optional[int] = None
    id_proceso_ejecutado: Optional[int] = None

class GeneracionDocumentoSchema(BaseModel):
    titulo: str
    motivo: str
    usuario: int
    notas: str
    destino: List[int]
    informacion: Dict[str, List[int]]  # Clave para distinguir entre registros y procesos

    class Config:
        from_attributes = True
