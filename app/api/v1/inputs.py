from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db  # Importa la función desde db.py
from app.models.models import Entradas, Registro, RegistroEntradas
from app.schemas.input import Input, InputRead, InputUpdate
from typing import List

router = APIRouter()

inputs = Entradas.__table__
registro_table = Registro.__table__
registro_entradas_table = RegistroEntradas.__table__

@router.get("/", response_model=List[InputRead])
async def read_inputs(db: Session = Depends(get_db)):
    # Ejecuta la consulta y obtén los resultados como un iterable de diccionarios
    result = db.execute(inputs.select()).mappings()
    # Utiliza model_validate para validar y crear una lista de InputRead
    inputs_list = [InputRead.model_validate(row) for row in result]
    return inputs_list

@router.get("/search/", response_model=List[InputRead])
async def search_inputs(name: str = None, id: int = None, db: Session = Depends(get_db)):
    # Crear la consulta base
    query = select(inputs)
    # Filtrar por nombre y id, si se proporciona
    if name:
        query = query.where(inputs.c.nombre.ilike(f'%{name}%'))  # Búsqueda sin importar mayúsculas
    if id is not None:
        query = query.where(inputs.c.id == id)  # Búsqueda por id
    # Ejecutar la consulta y obtener el resultado
    result = db.execute(query).mappings()
    # Validar el resultado y devolverlo
    inputs_list = [InputRead.model_validate(row) for row in result]
    if inputs_list:
        return inputs_list
    else:
        raise HTTPException(status_code=404, detail="Input not found")


def crear_registro_entrada(db: Session, entrada_id: int, descripcion: str, usuario_id: int = 0):
    # Crear el registro
    new_registro = {
        "id_usuario": usuario_id,
        "descripcion": descripcion
    }
    result_registro = db.execute(registro_table.insert().values(new_registro))
    registro_id = result_registro.inserted_primary_key[0]
    
    # Crear el registro_entrada
    new_registro_entrada = {
        "id_registro": registro_id,
        "id_entrada": entrada_id
    }
    db.execute(registro_entradas_table.insert().values(new_registro_entrada))
    db.commit()


@router.post("/", response_model=InputRead)
async def create_input(input: Input, db: Session = Depends(get_db)):
    try:
        # Inicia la transacción
        new_input = input.model_dump(exclude_unset=True, by_alias=True)
        result = db.execute(inputs.insert().values(new_input))
        db.commit()
        
        input_id = result.inserted_primary_key[0]
        created_input = db.execute(inputs.select().where(inputs.c.id == input_id)).mappings().first()

        # Crear el registro y registro_entrada
        name = created_input["nombre"]
        crear_registro_entrada(db, input_id, f'CREACION DE ENTRADA "{name}"')

        return InputRead.model_validate(created_input)
    
    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de error
        raise HTTPException(status_code=500, detail="Error al crear el input y su registro")


@router.put("/", response_model=InputRead)
async def update_input(input: InputUpdate, db: Session = Depends(get_db)):
    try:
        # Buscar si el input existe
        existing_input = db.execute(inputs.select().where(inputs.c.id == input.id)).mappings().first()
        if not existing_input:
            raise HTTPException(status_code=404, detail="Input not found")

        # Iniciar la transacción
        update_data = input.model_dump(exclude_unset=True, by_alias=True)

        db.execute(
            inputs.update().where(inputs.c.id == input.id)
            .values(update_data)
        )
        db.commit()

        # Obtener el input actualizado
        updated_input = db.execute(inputs.select().where(inputs.c.id == input.id)).mappings().first()

        # Crear el registro y registro_entrada para la actualización
        name = existing_input["nombre"]
        name_update = updated_input["nombre"]
        crear_registro_entrada(db, input.id, f'ACTUALIZACION DE ENTRADA "{name}  -> {name_update}"')

        return InputRead.model_validate(updated_input)

    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de error
        raise HTTPException(status_code=500, detail="Error al actualizar el input y su registro")
