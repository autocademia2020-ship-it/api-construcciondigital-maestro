from fastapi import FastAPI, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from database import engine, get_db

# Crear las tablas si no existen
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Parte Diario de Obra",
    description="Backend con control de Producción, Personal, Maquinaria y Reportes Acumulados",
    version="2.1.1"
)

# ----------------------------------------------------
# ESQUEMAS PYDANTIC (Validaciones)
# ----------------------------------------------------
class ProduccionCrear(BaseModel):
    codigo_item: str
    descripcion_tarea: str
    unidad_medida: str
    cantidad_avanzada: float
    ubicacion_sector: Optional[str] = None

class PersonalCrear(BaseModel):
    categoria: str
    cuadrilla_subcontrato: Optional[str] = "Propio"
    cantidad_operarios: int
    horas_hombre: float

class MaquinariaCrear(BaseModel):
    equipo: str
    horas_operativas: float
    horas_standby: Optional[float] = 0.0
    combustible_litros: Optional[float] = 0.0

class ParteDiarioCrear(BaseModel):
    obra_id: int = Field(..., description="ID numérico obligatorio de la obra", example=101)
    fecha: str = Field(..., description="Fecha del parte diario (YYYY-MM-DD)", example="2026-08-10")
    jefe_obra: str = Field(..., example="Antonio")
    clima: str = Field(..., example="Despejado")
    observaciones: Optional[str] = None
    produccion: Optional[List[ProduccionCrear]] = []
    personal: Optional[List[PersonalCrear]] = []
    maquinaria: Optional[List[MaquinariaCrear]] = []


# ----------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------

@app.get("/api/v1/partes-diarios")
def listar_partes_diarios(db: Session = Depends(get_db)):
    partes = db.query(models.ParteDiarioModel).all()
    return partes

@app.post("/api/v1/partes-diarios")
def crear_parte_diario(parte: ParteDiarioCrear, db: Session = Depends(get_db)):
    nuevo_parte = models.ParteDiarioModel(
        obra_id=parte.obra_id,
        fecha=parte.fecha,
        jefe_obra=parte.jefe_obra,
        clima=parte.clima,
        observaciones=parte.observaciones
    )
    db.add(nuevo_parte)
    db.flush()

    for item in parte.produccion:
        p = models.ProduccionModel(**item.model_dump(), parte_diario_id=nuevo_parte.id)
        db.add(p)

    for item in parte.personal:
        pers = models.PersonalModel(**item.model_dump(), parte_diario_id=nuevo_parte.id)
        db.add(pers)

    for item in parte.maquinaria:
        m = models.MaquinariaModel(**item.model_dump(), parte_diario_id=nuevo_parte.id)
        db.add(m)

    db.commit()
    db.refresh(nuevo_parte)

    return {
        "status": "exitoso",
        "mensaje": "Parte diario maestro registrado correctamente",
        "data": nuevo_parte
    }

@app.get("/api/v1/obras/{obra_id}/resumen-acumulado")
def obtener_resumen_obra(
    obra_id: int = Path(..., description="ID de la obra a consultar", example=101),
    db: Session = Depends(get_db)
):
    partes_count = db.query(models.ParteDiarioModel).filter(models.ParteDiarioModel.obra_id == obra_id).count()
    if partes_count == 0:
        raise HTTPException(status_code=404, detail=f"No se encontraron partes diarios registrados para la obra ID {obra_id}")

    total_hh = db.query(
        func.coalesce(func.sum(models.PersonalModel.horas_hombre), 0.0)
    ).join(
        models.ParteDiarioModel, models.PersonalModel.parte_diario_id == models.ParteDiarioModel.id
    ).filter(
        models.ParteDiarioModel.obra_id == obra_id
    ).scalar()

    resumen_maquinaria = db.query(
        func.coalesce(func.sum(models.MaquinariaModel.horas_operativas), 0.0).label("total_horas_operativas"),
        func.coalesce(func.sum(models.MaquinariaModel.combustible_litros), 0.0).label("total_combustible")
    ).join(
        models.ParteDiarioModel, models.MaquinariaModel.parte_diario_id == models.ParteDiarioModel.id
    ).filter(
        models.ParteDiarioModel.obra_id == obra_id
    ).first()

    produccion_acumulada = db.query(
        models.ProduccionModel.codigo_item,
        models.ProduccionModel.descripcion_tarea,
        models.ProduccionModel.unidad_medida,
        func.sum(models.ProduccionModel.cantidad_avanzada).label("total_acumulado")
    ).join(
        models.ParteDiarioModel, models.ProduccionModel.parte_diario_id == models.ParteDiarioModel.id
    ).filter(
        models.ParteDiarioModel.obra_id == obra_id
    ).group_by(
        models.ProduccionModel.codigo_item,
        models.ProduccionModel.descripcion_tarea,
        models.ProduccionModel.unidad_medida
    ).all()

    items_produccion = [
        {
            "codigo_item": p.codigo_item,
            "descripcion_tarea": p.descripcion_tarea,
            "unidad_medida": p.unidad_medida,
            "total_acumulado": float(p.total_acumulado)
        }
        for p in produccion_acumulada
    ]

    return {
        "obra_id": obra_id,
        "partes_diarios_registrados": partes_count,
        "totales_generales": {
            "horas_hombre_acumuladas": float(total_hh),
            "horas_maquinaria_operativas": float(resumen_maquinaria.total_horas_operativas),
            "combustible_litros_total": float(resumen_maquinaria.total_combustible)
        },
        "avance_produccion_por_item": items_produccion
    }