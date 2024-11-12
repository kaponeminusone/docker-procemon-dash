from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey, Enum as SQLAlchemyEnum, TIMESTAMP, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()

# Define enum types
class TipoEnum(str, Enum):
    type1 = 'admin'
    type2 = 'user'
    type3 = 'auditor'

class TipoEnumIndicador(str, Enum):
    type1 = 'range'
    type2 = 'checkbox'
    type3 = 'criteria'

class TipoEnumEntrada(str, Enum):
    type1 = 'int'
    type2 = 'float'

class Indicadores(Base):
    __tablename__ = 'indicadores'

    id = Column(BigInteger, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(SQLAlchemyEnum(TipoEnumIndicador), nullable=False)
    descripcion = Column(String, nullable=True)  # Nuevo campo opcional

class Entradas(Base):
    __tablename__ = 'entradas'

    id = Column(BigInteger, primary_key=True)
    nombre = Column(String)
    tipo = Column(SQLAlchemyEnum(TipoEnumEntrada))
    descripcion = Column(String, nullable=True)  # Nuevo campo opcional

class Procesos(Base):
    __tablename__ = 'procesos'

    id = Column(BigInteger, primary_key=True)
    nombre = Column(String, nullable=False)
    num_etapas = Column(Integer)
    descripcion = Column(String, nullable=True)  # Nuevo campo opcional

class Etapas(Base):
    __tablename__ = 'etapas'

    id = Column(BigInteger, primary_key=True)
    num_etapa = Column(BigInteger, nullable=False)
    id_proceso = Column(BigInteger, ForeignKey('procesos.id'))
    proceso = relationship('Procesos', backref='etapas')

class Usuario(Base):
    __tablename__ = 'usuario'

    id = Column(BigInteger, primary_key=True)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    tipo = Column(SQLAlchemyEnum(TipoEnum), nullable=False)
    password = Column(String, nullable=True)
    #TODO: Corregir para que el campo de password no pueda ser NULL

class EtapaIndicadores(Base):
    __tablename__ = 'etapa_indicadores'

    id_etapa = Column(BigInteger, ForeignKey('etapas.id'), primary_key=True)
    id_indicador_entrada = Column(BigInteger, ForeignKey('indicadores.id'), primary_key=True)

class EtapasEntradas(Base):
    __tablename__ = 'etapas_entradas'

    id_etapa = Column(BigInteger, ForeignKey('etapas.id'), primary_key=True)
    id_entrada = Column(BigInteger, ForeignKey('entradas.id'), primary_key=True)

class EtapasSalidas(Base):
    __tablename__ = 'etapas_salidas'

    id_etapa = Column(BigInteger, ForeignKey('etapas.id'), primary_key=True)
    id_entrada = Column(BigInteger, ForeignKey('entradas.id'), primary_key=True)


class IndicadoresEntradas(Base):
    __tablename__ = 'indicadores_entradas'

    id = Column(BigInteger, primary_key=True)
    id_entrada = Column(BigInteger, ForeignKey('entradas.id'), nullable=False)
    id_indicador = Column(BigInteger, ForeignKey('indicadores.id'))

class Registro(Base):
    __tablename__ = 'registro'

    id = Column(BigInteger, primary_key=True)
    id_usuario = Column(BigInteger, ForeignKey('usuario.id'), nullable=False)
    descripcion = Column(String)
    creado = Column(TIMESTAMP, default="now()")
    modificado = Column(TIMESTAMP, default="now()")

class RegistroEntradas(Base):
    __tablename__ = 'registro_entradas'

    id_registro = Column(BigInteger, ForeignKey('registro.id'), primary_key=True)
    id_entrada = Column(BigInteger, ForeignKey('entradas.id'))

class RegistroIndicadores(Base):
    __tablename__ = 'registro_indicadores'

    id_registro = Column(BigInteger, ForeignKey('registro.id'), primary_key=True)
    id_indicador = Column(BigInteger, ForeignKey('indicadores.id'))

class RegistroProcesos(Base):
    __tablename__ = 'registro_procesos'

    id_registro = Column(BigInteger, ForeignKey('registro.id'), primary_key=True)
    id_proceso = Column(BigInteger, ForeignKey('procesos.id'))


 #TODO: add Barrel

class ProcesosEjecutados(Base):
    __tablename__ = 'procesos_ejecutados'

    id = Column(BigInteger, primary_key=True)
    id_proceso = Column(BigInteger, ForeignKey('procesos.id'), nullable=False)
    no_conformidades = Column(Integer, default=0)
    conformidades = Column(Integer, default=0)
    num_etapas_con_conformidades = Column(Integer, default=0)
    tasa_de_exito = Column(Float)  # Puedes usar un tipo de dato diferente según tu necesidad
    cantidad_salida = Column(Float)
    cantidad_entrada = Column(Float)
    # Otros campos que consideres necesarios, como timestamps para registrar la fecha de ejecución

class Materiales(Base):
    __tablename__ = 'materiales'

    id = Column(BigInteger, primary_key=True)
    id_entrada = Column(BigInteger, ForeignKey('entradas.id'), nullable=False)
    cantidad_entrada = Column(Float)
    cantidad_salida = Column(Float)
    usos = Column(Integer)
    entrada = relationship('Entradas', backref='materiales')  # Relación hacia las entradas

class RegistroProcesoEjecutado(Base):
    __tablename__ = 'registro_proceso_ejecutado'

    id_proceso_ejecutado = Column(BigInteger, ForeignKey('procesos_ejecutados.id'), primary_key=True)
    id_registro = Column(BigInteger, ForeignKey('registro.id'), primary_key=True)

    # Puedes agregar relaciones hacia las otras tablas si es necesario
    proceso_ejecutado = relationship('ProcesosEjecutados', backref='registros')
    registro = relationship('Registro', backref='procesos_ejecutados')
