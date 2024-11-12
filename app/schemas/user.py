from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

# Definir un Enum para los roles de usuario (opcional)
class UserRole(str, Enum):
    type1 = "admin"
    type2 = "user"
    type3 = "auditor"

class User(BaseModel):
    id: Optional[int]
    username: str = Field(..., alias='nombre', min_length=3, max_length=50)
    email: EmailStr
    role: Optional[UserRole] = Field(default=UserRole.type2, alias='tipo')  #TODO: Evitar asignar rol desde la creacion'
    password: str

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original

class UserLogin(BaseModel):
    email: EmailStr = Field(..., alias='username')
    password: str

    class Config:
        populate_by_name = True  # Permite usar el nombre de campo original

class UserRead(BaseModel):
    id: int
    username: str = Field(..., alias='nombre', min_length=3, max_length=50)
    email: EmailStr
    role: UserRole = Field(alias='tipo')  # Mapeado a 'tipo'

    class Config:
        populate_by_name = True  # Permite la compatibilidad con modelos de base de datos

class UserUpdate(BaseModel):
    id: int  # Este campo es obligatorio
    username: Optional[str] = Field(None, alias='nombre', min_length=3, max_length=50)  # Opcional
    email: Optional[EmailStr] = None  # Opcional
    role: Optional[UserRole] = Field(None, alias='tipo')  # Opcional

    class Config:
        populate_by_name = True

# from pydantic import BaseModel, field_validator
# from datetime import date, timedelta

# class User(BaseModel):
#   id: int
#   name: str
#   email: str

#   @field_validator('name')
#   def nombre_no_contiene_numeros(cls, valor):
#     if any(char.isdigit() for char in valor):
#       raise ValueError('No puede contener numeros')
#     return valor
  
#   @field_validator('fecha_nacimiento')
#   def fecha_menor_al_anio(cls, valor):
#     cien_anios_atras = date.today - timedelta(days=365.25 * 100);
#     if valor >= date.today():
#       raise ValueError('La fecha debe ser menor al anio actual')
#     if valor <= cien_anios_atras:
#       raise ValueError('La fecha de nacimiento no puede ser superior a 100 años')
#     return valor