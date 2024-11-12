from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db  # Importa la función desde db.py
from app.models.models import Procesos, Entradas, Indicadores, Etapas, EtapasEntradas, EtapaIndicadores, EtapasSalidas, Registro, RegistroProcesos  # Asegúrate de importar tus modelos correctamente
from app.schemas.proceso import ProcesoCreate, ProcesoResponse, EtapaResponse, EntradaResponse, IndicadorResponse, ProcesoResponseAll, SalidaResponse  # Importa tus esquemas de Pydantic
from typing import List

router = APIRouter()

proceso_table = Procesos.__table__
etapas_table = Etapas.__table__
entradas_table = Entradas.__table__
indicadores_table = Indicadores.__table__
etapas_entradas_table = EtapasEntradas.__table__
etapas_indicadores_table = EtapaIndicadores.__table__
etapas_salidas_table = EtapasSalidas.__table__
registro_table = Registro.__table__
registro_procesos_table = RegistroProcesos.__table__

def crear_registro_proceso(db: Session, proceso_id: int, descripcion: str, usuario_id: int = 0):
    # Crear el registro
    new_registro = {
        "id_usuario": usuario_id,
        "descripcion": descripcion
    }
    result_registro = db.execute(registro_table.insert().values(new_registro))
    registro_id = result_registro.inserted_primary_key[0]
    
    # Crear el registro para el proceso
    new_registro_proceso = {
        "id_registro": registro_id,
        "id_proceso": proceso_id
    }
    db.execute(registro_procesos_table.insert().values(new_registro_proceso))
    db.commit()


@router.post("/")
async def create_proceso(proceso: ProcesoCreate, db: Session = Depends(get_db)):
   # Crea un nuevo diccionario para el proceso
    new_proceso = {
        "nombre": proceso.nombre,
        "num_etapas": len(proceso.etapas),
    }

    # Solo agrega "descripcion" si proceso.descripcion tiene un valor
    if proceso.descripcion:
        new_proceso["descripcion"] = proceso.descripcion
    # Usamos un bloque de transacción
    with db.begin():  # Comienza la transacción
        # Inserta el nuevo proceso en la base de datos
        result = db.execute(proceso_table.insert().values(new_proceso))
        
        # Obtiene el último proceso insertado
        proceso_id = result.inserted_primary_key[0]
        
        # Inserta las etapas relacionadas
        for etapa in proceso.etapas:
            new_etapa = {
                "num_etapa": etapa.num_etapa,
                "id_proceso": proceso_id
            }
            etapa_result = db.execute(etapas_table.insert().values(new_etapa))

            etapa_id = etapa_result.inserted_primary_key[0]

            # Inserta las entradas, indicadores y salidas para cada etapa
            for entrada in etapa.entradas:
                db.execute(etapas_entradas_table.insert().values(id_etapa=etapa_id, id_entrada=entrada.id))

            for indicador in etapa.indicadores:
                db.execute(etapas_indicadores_table.insert().values(id_etapa=etapa_id, id_indicador_entrada=indicador.id))

            for salida in etapa.salidas:
                db.execute(etapas_salidas_table.insert().values(id_etapa=etapa_id, id_entrada=salida.id))

    # Obtiene el proceso creado con las etapas y detalles completos
    created_proceso = db.execute(proceso_table.select().where(proceso_table.c.id == proceso_id)).mappings().first()

    # Registra la creación del proceso
    crear_registro_proceso(db, proceso_id, f'CREACION DE PROCESO "{created_proceso["nombre"]}"')

    # Obtiene las etapas relacionadas
    etapas = db.execute(etapas_table.select().where(etapas_table.c.id_proceso == proceso_id)).mappings().all()

    # Crea la respuesta final
    etapas_response = []
    for etapa in etapas:
        # Obtiene las entradas relacionadas
        entradas = db.execute(etapas_entradas_table.select().where(etapas_entradas_table.c.id_etapa == etapa.id)).mappings().all()
        entrada_responses = []
        for entrada in entradas:
            entrada_data = db.execute(entradas_table.select().where(entradas_table.c.id == entrada.id_entrada)).mappings().first()
            entrada_responses.append(EntradaResponse(id=entrada_data.id, nombre=entrada_data.nombre, tipo=entrada_data.tipo))

        # Obtiene los indicadores relacionados
        indicadores = db.execute(etapas_indicadores_table.select().where(etapas_indicadores_table.c.id_etapa == etapa.id)).mappings().all()
        indicador_responses = []
        for indicador in indicadores:
            indicador_data = db.execute(indicadores_table.select().where(indicadores_table.c.id == indicador.id_indicador_entrada)).mappings().first()
            indicador_responses.append(IndicadorResponse(id=indicador_data.id, nombre=indicador_data.nombre, tipo=indicador_data.tipo, entrada_id=entrada_data.id))

        # Obtiene las salidas relacionadas
        salidas = db.execute(etapas_salidas_table.select().where(etapas_salidas_table.c.id_etapa == etapa.id)).mappings().all()
        salida_responses = []
        for salida in salidas:
            salida_data = db.execute(entradas_table.select().where(entradas_table.c.id == salida.id_entrada)).mappings().first()
            salida_responses.append(SalidaResponse(id=salida_data.id, nombre=salida_data.nombre, tipo=salida_data.tipo))

        etapas_response.append(EtapaResponse(
            id=etapa.id,
            num_etapa=etapa.num_etapa,
            entradas=entrada_responses,
            indicadores=indicador_responses,
            salidas=salida_responses
        ))

    # Crea el objeto de respuesta final
    proceso_response = {
        "id": proceso_id,
        "nombre": created_proceso.nombre,
        "num_etapas": len(etapas_response),
        "etapas": etapas_response
    }

    # Valida el objeto de respuesta
    return ProcesoResponse.model_validate(proceso_response)


@router.get("/{proceso_id}", response_model=ProcesoResponse)
async def get_proceso(proceso_id: int, db: Session = Depends(get_db)):
    # Obtiene el proceso por ID
    created_proceso = db.execute(proceso_table.select().where(proceso_table.c.id == proceso_id)).mappings().first()

    if not created_proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Obtiene las etapas relacionadas
    etapas = db.execute(etapas_table.select().where(etapas_table.c.id_proceso == proceso_id)).mappings().all()

    # Crea la respuesta final
    etapas_response = []
    for etapa in etapas:
        # Obtiene las entradas relacionadas
        entradas = db.execute(etapas_entradas_table.select().where(etapas_entradas_table.c.id_etapa == etapa.id)).mappings().all()
        entrada_responses = []
        for entrada in entradas:
            entrada_data = db.execute(entradas_table.select().where(entradas_table.c.id == entrada.id_entrada)).mappings().first()
            entrada_responses.append(EntradaResponse(id=entrada_data.id, nombre=entrada_data.nombre, tipo=entrada_data.tipo))

        # Obtiene los indicadores relacionados
        indicadores = db.execute(etapas_indicadores_table.select().where(etapas_indicadores_table.c.id_etapa == etapa.id)).mappings().all()
        indicador_responses = []
        for indicador in indicadores:
            indicador_data = db.execute(indicadores_table.select().where(indicadores_table.c.id == indicador.id_indicador_entrada)).mappings().first()
            indicador_responses.append(IndicadorResponse(id=indicador_data.id, nombre=indicador_data.nombre, tipo=indicador_data.tipo, entrada_id=entrada_data.id))

        # Obtiene las salidas relacionadas
        salidas = db.execute(etapas_salidas_table.select().where(etapas_salidas_table.c.id_etapa == etapa.id)).mappings().all()
        salida_responses = []
        for salida in salidas:
            salida_data = db.execute(entradas_table.select().where(entradas_table.c.id == salida.id_entrada)).mappings().first()
            salida_responses.append(SalidaResponse(id=salida_data.id, nombre=salida_data.nombre, tipo=salida_data.tipo))

        etapas_response.append(EtapaResponse(
            id=etapa.id,
            num_etapa=etapa.num_etapa,
            entradas=entrada_responses,
            indicadores=indicador_responses,
            salidas=salida_responses
        ))

    # Crea el objeto de respuesta final
    proceso_response = {
        "id": proceso_id,
        "nombre": created_proceso.nombre,
        "num_etapas": len(etapas_response),
        "etapas": etapas_response
    }

    return ProcesoResponse.model_validate(proceso_response)


@router.get("/", response_model=List[ProcesoResponseAll])
async def get_all_procesos(db: Session = Depends(get_db)):
    # Obtiene todos los procesos
    procesos = db.execute(proceso_table.select()).mappings().all()

    procesos_response = []
    
    for proceso in procesos:
        # Obtiene las etapas relacionadas
        etapas = db.execute(etapas_table.select().where(etapas_table.c.id_proceso == proceso.id)).mappings().all()
        
        num_etapas = len(etapas)
        num_entradas = 0
        num_salidas = 0
        num_indicadores = 0
        
        for etapa in etapas:
            # Cuenta las entradas
            entradas = db.execute(etapas_entradas_table.select().where(etapas_entradas_table.c.id_etapa == etapa.id)).mappings().all()
            num_entradas += len(entradas)

            # Cuenta los indicadores
            indicadores = db.execute(etapas_indicadores_table.select().where(etapas_indicadores_table.c.id_etapa == etapa.id)).mappings().all()
            num_indicadores += len(indicadores)

            # Cuenta las salidas
            salidas = db.execute(etapas_salidas_table.select().where(etapas_salidas_table.c.id_etapa == etapa.id)).mappings().all()
            num_salidas += len(salidas)

        # Crea la respuesta para cada proceso
        proceso_response = {
            "id": proceso.id,
            "descripcion": proceso.descripcion,
            "nombre": proceso.nombre,
            "num_etapas": num_etapas,
            "num_entradas": num_entradas,
            "num_salidas": num_salidas,
            "num_indicadores": num_indicadores,
        }

        procesos_response.append(ProcesoResponseAll.model_validate(proceso_response))

    return procesos_response
