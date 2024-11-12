from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db  # Importa la función desde db.py
from app.models.models import Indicadores, Registro, RegistroIndicadores
from app.schemas.indicator import Indicator, IndicatorRead, IndicatorUpdate
from typing import List

router = APIRouter()

indicators = Indicadores.__table__
registro_table = Registro.__table__
registro_indicadores_table = RegistroIndicadores.__table__

@router.get("/", response_model=List[IndicatorRead])
async def read_indicators(db: Session = Depends(get_db)):
    # Ejecuta la consulta y obtén los resultados como un iterable de diccionarios
    result = db.execute(indicators.select()).mappings()
    # Utiliza model_validate para validar y crear una lista de IndicatorRead
    indicators_list = [IndicatorRead.model_validate(row) for row in result]
    return indicators_list

@router.get("/search/", response_model=List[IndicatorRead])
async def search_indicators(name: str = None, id: int = None, db: Session = Depends(get_db)):
    # Crear la consulta base
    query = select(indicators)
    # Filtrar por nombre y id, si se proporciona
    if name:
        query = query.where(indicators.c.nombre.ilike(f'%{name}%'))  # Búsqueda sin importar mayúsculas
    if id is not None:
        query = query.where(indicators.c.id == id)  # Búsqueda por id
    # Ejecutar la consulta y obtener el resultado
    result = db.execute(query).mappings()
    # Validar el resultado y devolverlo
    indicators_list = [IndicatorRead.model_validate(row) for row in result]
    if indicators_list:
        return indicators_list
    else:
        raise HTTPException(status_code=404, detail="Indicator not found")


def crear_registro_indicador(db: Session, indicador_id: int, descripcion: str, usuario_id: int = 0):
    # Crear el registro
    new_registro = {
        "id_usuario": usuario_id,
        "descripcion": descripcion
    }
    result_registro = db.execute(registro_table.insert().values(new_registro))
    registro_id = result_registro.inserted_primary_key[0]
    
    # Crear el registro para el indicador
    new_registro_indicador = {
        "id_registro": registro_id,
        "id_indicador": indicador_id
    }
    db.execute(registro_indicadores_table.insert().values(new_registro_indicador))
    db.commit()

@router.post("/", response_model=IndicatorRead)
async def create_indicator(input: Indicator, db: Session = Depends(get_db)):
    try:
        # Inicia la transacción
        new_input = input.model_dump(exclude_unset=True, by_alias=True)
        result = db.execute(indicators.insert().values(new_input))
        db.commit()
        
        indicador_id = result.inserted_primary_key[0]
        created_input = db.execute(indicators.select().where(indicators.c.id == indicador_id)).mappings().first()

        # Crear el registro y registro_indicador
        crear_registro_indicador(db, indicador_id, f'CREACION DE INDICADOR "{created_input["nombre"]}"')

        return IndicatorRead.model_validate(created_input)
    
    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de error
        raise HTTPException(status_code=500, detail="Error al crear el indicador y su registro")


@router.put("/", response_model=IndicatorRead)
async def update_indicator(input: IndicatorUpdate, db: Session = Depends(get_db)):
    try:
        # Buscar si el indicador existe
        existing_input = db.execute(indicators.select().where(indicators.c.id == input.id)).mappings().first()
        if not existing_input:
            raise HTTPException(status_code=404, detail="Indicator not found")

        # Iniciar la transacción
        update_data = input.model_dump(exclude_unset=True, by_alias=True)

        db.execute(
            indicators.update().where(indicators.c.id == input.id)
            .values(update_data)
        )
        db.commit()

        # Obtener el indicador actualizado
        updated_input = db.execute(indicators.select().where(indicators.c.id == input.id)).mappings().first()

        # Crear el registro y registro_indicador para la actualización
        crear_registro_indicador(db, input.id, f'ACTUALIZACION DE INDICADOR "{existing_input["nombre"]} -> {updated_input["nombre"]}"')

        return IndicatorRead.model_validate(updated_input)

    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de error
        raise HTTPException(status_code=500, detail="Error al actualizar el indicador y su registro")

