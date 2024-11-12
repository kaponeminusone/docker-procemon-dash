from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Union
from app.db.database import get_db
from app.models.models import ProcesosEjecutados, Materiales, Registro, RegistroProcesoEjecutado, RegistroProcesos
from app.schemas.execution import EjecucionProcesoSchema, EtapaRegistroSchema, EtapaSchema, MaterialSchema, RegistroEjecucionSchema
import json
import os
import random

router = APIRouter()

# Variables de tablas para evitar el uso de __table__ directamente
procesos_ejecutados_table = ProcesosEjecutados.__table__
materiales_table = Materiales.__table__
registro_table = Registro.__table__
registro_procesos_ejecutados_table = RegistroProcesoEjecutado.__table__

def guardar_en_json(data: List[dict], filename: str):
    """Guarda los datos en un archivo JSON sin sobreescribir, añadiéndolos al final."""
    print("Guardando en Json...")

    # Crear el directorio si no existe
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Leer datos existentes si el archivo ya existe
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Agregar los nuevos datos a los existentes
    existing_data.extend(data)

    # Guardar la combinación de datos en el archivo JSON
    with open(filename, 'w') as f:
        json.dump(existing_data, f, indent=4)


def crear_registro_proceso(db: Session, proceso_id: int, descripcion: str, usuario_id: int = 0):
    """Crea un registro de proceso y asocia el registro a un ID de usuario."""
    new_registro = {
        "id_usuario": usuario_id,
        "descripcion": descripcion
    }
    result_registro = db.execute(registro_table.insert().values(new_registro))
    registro_id = result_registro.inserted_primary_key[0]
    
    new_registro_proceso = {
        "id_registro": registro_id,
        "id_proceso_ejecutado": proceso_id
    }
    db.execute(registro_procesos_ejecutados_table.insert().values(new_registro_proceso))

def actualizar_materiales(db: Session, materiales: List[MaterialSchema], es_entrada: bool):
    """Actualiza los materiales en función de las entradas o salidas."""
    for material in materiales:
        
        existing_material = db.execute(materiales_table.select().where(materiales_table.c.id_entrada == material.id)).first()
        
        if not existing_material:

            new_material = {
                "id_entrada": material.id,
                "cantidad_entrada": 0,
                "cantidad_salida": 0,
                "usos": 0,
            }
            db.execute(materiales_table.insert().values(new_material))

        existing_material = db.execute(materiales_table.select().where(materiales_table.c.id_entrada == material.id)).first()
        
        if es_entrada:
            db.execute(materiales_table.update().where(materiales_table.c.id_entrada == material.id).values(
                    cantidad_entrada=existing_material.cantidad_entrada + material.value,
                    usos=existing_material.usos + 1))
        else:
            db.execute(materiales_table.update().where(materiales_table.c.id_entrada == material.id).values(
                    cantidad_salida=existing_material.cantidad_salida + material.value,
                    usos=existing_material.usos + 1))    
            

# Ruta del archivo JSON de datos
DATA_JSON_PATH = "data/data_procesos.json"

from typing import Dict, Union, List
import random

def evaluar_indicador(entrada_value: float, indicador: Dict[str, Union[bool, str]]) -> (float, bool):
    no_conformidad = 0.0
    afectado = False

    # Checkbox
    if indicador.get("checkbox") is not None:
        if not indicador["checkbox"]:  # Si es False, introduce una no conformidad aleatoria
            no_conformidad += random.uniform(0, entrada_value * 0.1)
            afectado = True

    # Criteria
    criteria = indicador.get("criteria")
    if criteria:
        if "%" in criteria:
            porcentaje = float(criteria.strip("%")) / 100
            no_conformidad += entrada_value * porcentaje
        else:
            no_conformidad += float(criteria)
        afectado = True

    # Range
    rango = indicador.get("range")
    if rango:
        min_val, max_val = map(float, rango.split("-"))
        if entrada_value < min_val or entrada_value > max_val:
            no_conformidad += abs(entrada_value - max(min_val, min(entrada_value, max_val)))
            afectado = True

    return no_conformidad, afectado
def procesar_etapa(etapa: EtapaSchema) -> Dict:
    total_no_conformes = 0.0
    total_conformes = 0.0

    for entrada in etapa.entradas:
        entrada_value = entrada.value
        no_conformes = 0.0

        for indicador in etapa.indicadores:
            if indicador.entrada_id == entrada.id:
                no_conformidad, afectado = evaluar_indicador(entrada_value, indicador.dict())
                no_conformes += no_conformidad
                indicador.state = afectado  # Asigna el estado de afectación al indicador

        salida_value = max(0, entrada_value - no_conformes)
        total_no_conformes += no_conformes
        total_conformes += salida_value

        for salida in etapa.salidas:
            if salida.id == entrada.id:
                salida.value = salida_value

    return {
        "conformes": int(total_conformes),
        "no_conformes": int(total_no_conformes),
        "entradas": [entrada.dict() for entrada in etapa.entradas],
        "indicadores": [indicador.dict() for indicador in etapa.indicadores],
        "salidas": [salida.dict() for salida in etapa.salidas]
    }

# Endpoint de previsualización ajustado
@router.post("/preview-evaluation")
async def preview(etapa: EtapaSchema):
    resultado = procesar_etapa(etapa)
    return {"preview": resultado}

@router.post("/")
async def execute_proceso(data: EjecucionProcesoSchema, db: Session = Depends(get_db)):
    with db.begin():
        id_proceso = data.id_proceso
        etapas = data.etapas

        # Crear un registro inicial en ProcesosEjecutados
        new_proceso_ejecutado = {
            "id_proceso": id_proceso,
            "num_etapas_con_conformidades": 0,
            "tasa_de_exito": 0.0,
            "no_conformidades": 0,
            "conformidades": 0,
            "cantidad_entrada": sum(entrada.value for etapa in etapas for entrada in etapa.entradas),
            "cantidad_salida": 0  # Esto se actualizará después
        }
        proceso_ejecutado = db.execute(ProcesosEjecutados.__table__.insert().values(new_proceso_ejecutado))
        proceso_ejecutado_id = proceso_ejecutado.inserted_primary_key[0]

        # Inicializamos acumuladores
        total_conformes = 0
        total_no_conformes = 0
        num_etapas_con_conformidades = 0

        data_to_save = {
            "id_proceso": id_proceso,
            "id_proceso_ejecutado": proceso_ejecutado_id,
            "num_etapas": len(etapas),
            "no_conformes": 0,
            "conformes": 0,
            "etapas": []
        }

        for etapa in etapas:
            resultado_etapa = procesar_etapa(etapa)
            total_conformes += resultado_etapa["conformes"]
            total_no_conformes += resultado_etapa["no_conformes"]

            if resultado_etapa["conformes"] > 0:
                num_etapas_con_conformidades += 1

            # Actualizar materiales en función de entradas y salidas
            actualizar_materiales(db, etapa.entradas, es_entrada=True)
            actualizar_materiales(db, etapa.salidas, es_entrada=False)

            etapa_data = {
                "num_etapa": etapa.num_etapa,
                "conformes": resultado_etapa["conformes"],
                "no_conformes": resultado_etapa["no_conformes"],
                "state": any(indicador.get("state", False) for indicador in resultado_etapa["indicadores"]),
                "entradas": resultado_etapa["entradas"],
                "indicadores": resultado_etapa["indicadores"],
                "salidas": resultado_etapa["salidas"]
            }
            data_to_save["etapas"].append(etapa_data)

        # Calcular la tasa de éxito
        tasa_de_exito = (total_conformes / (total_conformes + total_no_conformes)) * 100 if (total_conformes + total_no_conformes) > 0 else 0

        # Guardar en JSON
        data_to_save["conformes"] = total_conformes
        data_to_save["no_conformes"] = total_no_conformes
        data_to_save["num_etapas_con_conformidades"] = num_etapas_con_conformidades
        data_to_save["tasa_de_exito"] = tasa_de_exito
        guardar_en_json([data_to_save], DATA_JSON_PATH)

        # Actualizar el registro en ProcesosEjecutados
        db.execute(
            ProcesosEjecutados.__table__.update()
            .where(ProcesosEjecutados.__table__.c.id == proceso_ejecutado_id)
            .values(
                num_etapas_con_conformidades=num_etapas_con_conformidades,
                tasa_de_exito=tasa_de_exito,
                no_conformidades=total_no_conformes,
                conformidades=total_conformes,
                cantidad_salida=total_conformes  # Aquí se asigna la cantidad de salida como el total conforme
            )
        )

        descripcion = f"Ejecución ID {proceso_ejecutado_id} de proceso ID {id_proceso} con {len(etapas)} etapas."
        crear_registro_proceso(db, proceso_ejecutado_id, descripcion)

    return {"message": "Proceso ejecutado y datos guardados correctamente."}

