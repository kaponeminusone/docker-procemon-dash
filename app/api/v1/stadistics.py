from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Materiales, Entradas, Procesos
from app.schemas.stadistics import (
    MaterialEntradaSalidaSchema,
    DiagramaNoConformidadesSchema,
    EstadoEtapasSchema,
    ProcesoExitoSchema
)
import json
import os

router = APIRouter()

# Endpoint para Estado de Entradas y Salidas
@router.get("/estadisticas/estado-entradas-salidas", response_model=list[MaterialEntradaSalidaSchema])
async def obtener_estado_entradas_salidas(db: Session = Depends(get_db)):
    materiales = db.query(Materiales, Entradas.nombre).join(Entradas, Materiales.id_entrada == Entradas.id).all()
    estado_entradas_salidas = [
        MaterialEntradaSalidaSchema(
            id=material.id,
            nombre=nombre,
            cantidad_entrada=material.cantidad_entrada,
            cantidad_salida=material.cantidad_salida,
            usos=material.usos
        )
        for material, nombre in materiales
    ]
    return estado_entradas_salidas

# Endpoint para Diagrama de No Conformidades
@router.get("/estadisticas/diagrama-no-conformidades", response_model=DiagramaNoConformidadesSchema)
async def obtener_diagrama_no_conformidades():
    json_path = os.path.join("data", "data_procesos.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Archivo de datos no encontrado.")

    with open(json_path, "r") as file:
        data_procesos = json.load(file)

    total_conformes = sum(proceso["conformes"] for proceso in data_procesos)
    total_no_conformes = sum(proceso["no_conformes"] for proceso in data_procesos)

    return DiagramaNoConformidadesSchema(conformes=total_conformes, no_conformes=total_no_conformes)

# Endpoint para Estado General por Etapas
@router.get("/estadisticas/estado-general-etapas", response_model=list[EstadoEtapasSchema])
async def obtener_estado_general_etapas():
    json_path = os.path.join("data", "data_procesos.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Archivo de datos no encontrado.")

    with open(json_path, "r") as file:
        data_procesos = json.load(file)

    estado_general_etapas = []
    for etapa_num in range(5):  # Ajustar según el número máximo de etapas
        conformes_por_etapa = sum(
            etapa["conformes"] for proceso in data_procesos for etapa in proceso["etapas"] if etapa["num_etapa"] == etapa_num
        )
        no_conformes_por_etapa = sum(
            etapa["no_conformes"] for proceso in data_procesos for etapa in proceso["etapas"] if etapa["num_etapa"] == etapa_num
        )
        estado_general_etapas.append(EstadoEtapasSchema(num_etapa=etapa_num, conformes=conformes_por_etapa, no_conformes=no_conformes_por_etapa))

    return estado_general_etapas

# Endpoint para Procesos con Mayor y Menor Éxito
@router.get("/estadisticas/procesos-exito", response_model=dict[str, list[ProcesoExitoSchema]])
async def obtener_procesos_exito(db: Session = Depends(get_db)):
    json_path = os.path.join("data", "data_procesos.json")
    if not os.path.exists(json_path):
        print("Archivo de datos no encontrado en la ruta:", json_path)
        raise HTTPException(status_code=404, detail="Archivo de datos no encontrado.")

    with open(json_path, "r") as file:
        data_procesos = json.load(file)
    print("Datos cargados desde JSON:", data_procesos)

    procesos_exito = {}
    for proceso in data_procesos:
        id_proceso = proceso["id_proceso"]
        exito_actual = proceso["conformes"] / (proceso["conformes"] + proceso["no_conformes"]) if (proceso["conformes"] + proceso["no_conformes"]) > 0 else 0
        print(f"Proceso ID: {id_proceso} - Exito actual: {exito_actual}")

        if id_proceso in procesos_exito:
            procesos_exito[id_proceso].append(exito_actual)
        else:
            procesos_exito[id_proceso] = [exito_actual]

    # Calcular el promedio de éxito y clasificar
    procesos_menos_exito = []
    procesos_mayor_exito = []
    for id_proceso, exitos in procesos_exito.items():
        promedio_exito = sum(exitos) / len(exitos)
        proceso_nombre = db.query(Procesos.nombre).filter(Procesos.id == id_proceso).scalar()
        print(f"ID Proceso: {id_proceso} - Nombre: {proceso_nombre} - Promedio de éxito: {promedio_exito}")

        # Verificar si el nombre del proceso existe
        if proceso_nombre is None:
            print(f"Proceso ID {id_proceso} no tiene un nombre en la base de datos y será omitido.")
            continue  # Omite el proceso si no tiene un nombre en la base de datos

        proceso_data = ProcesoExitoSchema(id_proceso=id_proceso, nombre=proceso_nombre, exito_promedio=promedio_exito)
        if promedio_exito < 0.5:
            print(f"Proceso ID {id_proceso} clasificado en 'menos éxito'")
            procesos_menos_exito.append(proceso_data)
        else:
            print(f"Proceso ID {id_proceso} clasificado en 'mayor éxito'")
            procesos_mayor_exito.append(proceso_data)

    print("Procesos con menos éxito:", procesos_menos_exito)
    print("Procesos con mayor éxito:", procesos_mayor_exito)

    return {
        "procesos_menos_exito": procesos_menos_exito,
        "procesos_mayor_exito": procesos_mayor_exito
    }
