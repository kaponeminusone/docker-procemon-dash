from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timedelta
import json
import os
from app.dependencies.auth import get_current_user
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Registro, RegistroEntradas, RegistroIndicadores, RegistroProcesos, RegistroProcesoEjecutado, ProcesosEjecutados
from typing import Optional
import pytz

router = APIRouter()

# Configuración inicial del horario de disponibilidad
HORARIO_INICIO = 4  # 10 AM
DURACION_HORAS = 1
RESUMEN_PATH = "data/resumen_dia.json"
TIMEZONE = pytz.timezone("America/Bogota")  # GMT-5

# Función para verificar si el usuario es admin
async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges"
        )
    return current_user

# Función para verificar la disponibilidad actual
def esta_disponible():
    ahora = datetime.now(TIMEZONE)
    hora_inicio = ahora.replace(hour=HORARIO_INICIO, minute=0, second=0, microsecond=0)
    hora_fin = hora_inicio + timedelta(hours=DURACION_HORAS)
    return hora_inicio <= ahora <= hora_fin

# Endpoint para configurar el horario de disponibilidad, solo accesible para administradores
@router.post("/config/horario", tags=["Time"])
async def configurar_horario(hora_inicio: int, duracion_horas: int, admin_user: dict = Depends(get_admin_user)):
    global HORARIO_INICIO, DURACION_HORAS
    if 0 <= hora_inicio < 24 and 0 < duracion_horas <= 24:
        HORARIO_INICIO = hora_inicio
        DURACION_HORAS = duracion_horas
        return {
            "message": "Horario de disponibilidad actualizado",
            "hora_inicio": HORARIO_INICIO,
            "duracion_horas": DURACION_HORAS
        }
    else:
        raise HTTPException(status_code=400, detail="Hora de inicio o duración inválida. Deben estar entre 0-23 para hora_inicio y 1-24 para duracion_horas.")

# Endpoint para verificar disponibilidad, devuelve el estado y el horario de inicio y fin
@router.get("/disponibilidad", tags=["Time"])
async def verificar_disponibilidad():
    ahora = datetime.now(TIMEZONE)
    disponible = esta_disponible()
    hora_inicio = ahora.replace(hour=HORARIO_INICIO, minute=0, second=0, microsecond=0)
    hora_fin = hora_inicio + timedelta(hours=DURACION_HORAS)
    return {
        "disponible": disponible,
        "inicio": hora_inicio.strftime('%H:%M'),
        "fin": hora_fin.strftime('%H:%M')
    }

# Función para generar el resumen diario y guardarlo en JSON
def generar_resumen_diario(db: Session):
    ahora = datetime.now(TIMEZONE)
    hoy = ahora.date()
    ayer = hoy - timedelta(days=1)

    # Filtrar registros en base a la zona horaria
    registros_hoy = db.query(Registro).filter(Registro.creado >= ahora.replace(hour=0, minute=0, second=0, microsecond=0)).all()
    registros_ayer = db.query(Registro).filter(Registro.creado >= ayer, Registro.creado < ahora.replace(hour=0, minute=0, second=0, microsecond=0)).all()

    # Contar los registros del día actual desde las tablas de asociación
    resumen_hoy = {
        "fecha": str(hoy),
        "indicadores": db.query(RegistroIndicadores).join(Registro).filter(Registro.creado >= hoy).count(),
        "procesos": db.query(RegistroProcesos).join(Registro).filter(Registro.creado >= hoy).count(),
        "entradas_salidas": db.query(RegistroEntradas).join(Registro).filter(Registro.creado >= hoy).count(),
        "procesos_ejecutados": db.query(RegistroProcesoEjecutado).join(Registro).filter(Registro.creado >= hoy).count(),
    }

    resumen_ayer = {
        "fecha": str(ayer),
        "indicadores": db.query(RegistroIndicadores).join(Registro).filter(Registro.creado >= ayer, Registro.creado < hoy).count(),
        "procesos": db.query(RegistroProcesos).join(Registro).filter(Registro.creado >= ayer, Registro.creado < hoy).count(),
        "entradas_salidas": db.query(RegistroEntradas).join(Registro).filter(Registro.creado >= ayer, Registro.creado < hoy).count(),
        "procesos_ejecutados": db.query(RegistroProcesoEjecutado).join(Registro).filter(Registro.creado >= ayer, Registro.creado < hoy).count(),
    }

    # Obtener conformes y no conformes desde ProcesosEjecutados en el día actual y el anterior
    conformes_hoy = db.query(ProcesosEjecutados.conformidades).join(RegistroProcesoEjecutado, RegistroProcesoEjecutado.id_proceso_ejecutado == ProcesosEjecutados.id)\
                      .join(Registro, RegistroProcesoEjecutado.id_registro == Registro.id).filter(Registro.creado >= hoy).all()
    no_conformes_hoy = db.query(ProcesosEjecutados.no_conformidades).join(RegistroProcesoEjecutado, RegistroProcesoEjecutado.id_proceso_ejecutado == ProcesosEjecutados.id)\
                          .join(Registro, RegistroProcesoEjecutado.id_registro == Registro.id).filter(Registro.creado >= hoy).all()

    conformes_ayer = db.query(ProcesosEjecutados.conformidades).join(RegistroProcesoEjecutado, RegistroProcesoEjecutado.id_proceso_ejecutado == ProcesosEjecutados.id)\
                      .join(Registro, RegistroProcesoEjecutado.id_registro == Registro.id).filter(Registro.creado >= ayer, Registro.creado < hoy).all()
    no_conformes_ayer = db.query(ProcesosEjecutados.no_conformidades).join(RegistroProcesoEjecutado, RegistroProcesoEjecutado.id_proceso_ejecutado == ProcesosEjecutados.id)\
                          .join(Registro, RegistroProcesoEjecutado.id_registro == Registro.id).filter(Registro.creado >= ayer, Registro.creado < hoy).all()

    resumen_hoy["produccion"] = sum(conforme[0] for conforme in conformes_hoy)
    resumen_hoy["no_conformes"] = sum(no_conforme[0] for no_conforme in no_conformes_hoy)
    resumen_ayer["produccion"] = sum(conforme[0] for conforme in conformes_ayer)
    resumen_ayer["no_conformes"] = sum(no_conforme[0] for no_conforme in no_conformes_ayer)

    # Guardar en JSON el resumen del día y el día anterior
    data_resumen = {"hoy": resumen_hoy, "ayer": resumen_ayer}
    os.makedirs(os.path.dirname(RESUMEN_PATH), exist_ok=True)
    with open(RESUMEN_PATH, 'w') as f:
        json.dump(data_resumen, f, indent=4)

    return data_resumen

# Endpoint para generar el resumen del día (solo accesible para administradores o fuera de horario)
@router.post("/generar-resumen", tags=["Estadísticas"])
async def generar_resumen(admin_user: dict = Depends(get_admin_user), db: Session = Depends(get_db)):
    resumen = generar_resumen_diario(db)
    return {"message": "Resumen generado exitosamente", "resumen": resumen}

# Endpoint para obtener el resumen del día, solo consulta el archivo
@router.get("/resumen-dia", tags=["Estadísticas"])
async def obtener_resumen_del_dia():
    if esta_disponible():
        raise HTTPException(status_code=403, detail="El sistema está disponible; no se puede ver el resumen ahora.")
    
    if not os.path.exists(RESUMEN_PATH):
        raise HTTPException(status_code=404, detail="Resumen no disponible; no se ha generado el archivo.")
    
    with open(RESUMEN_PATH, 'r') as file:
        resumen = json.load(file)
    return resumen
