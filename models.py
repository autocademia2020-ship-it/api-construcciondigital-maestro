from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# ==========================================
# TABLA PRINCIPAL: CABECERA DEL PARTE DIARIO
# ==========================================
class ParteDiarioModel(Base):
    __tablename__ = "partes_diarios"

    id = Column(Integer, primary_key=True, index=True)
    obra_id = Column(Integer, nullable=False, index=True)
    fecha = Column(String, nullable=False)
    jefe_obra = Column(String, nullable=False)
    clima = Column(String, nullable=True)
    observaciones = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones con las tablas secundarias
    produccion = relationship("ProduccionModel", back_populates="parte_diario", cascade="all, delete-orphan")
    personal = relationship("PersonalModel", back_populates="parte_diario", cascade="all, delete-orphan")
    maquinaria = relationship("MaquinariaModel", back_populates="parte_diario", cascade="all, delete-orphan")


# ==========================================
# TABLA SECUNDARIA 1: PRODUCCIÓN / AVANCE
# ==========================================
class ProduccionModel(Base):
    __tablename__ = "parte_produccion"

    id = Column(Integer, primary_key=True, index=True)
    parte_diario_id = Column(Integer, ForeignKey("partes_diarios.id"), nullable=False)
    codigo_item = Column(String, nullable=False)        # Ej: "H-01", "EXC-02"
    descripcion_tarea = Column(String, nullable=False)  # Ej: "Hormigonado de tabiques"
    unidad_medida = Column(String, nullable=False)      # Ej: "m3", "m2", "tn"
    cantidad_avanzada = Column(Float, nullable=False)   # Ej: 24.50
    ubicacion_sector = Column(String, nullable=True)    # Ej: "Sector A - Nivel +3.00"

    # Relación inversa hacia el parte diario
    parte_diario = relationship("ParteDiarioModel", back_populates="produccion")


# ==========================================
# TABLA SECUNDARIA 2: ASISTENCIA Y PERSONAL
# ==========================================
class PersonalModel(Base):
    __tablename__ = "parte_personal"

    id = Column(Integer, primary_key=True, index=True)
    parte_diario_id = Column(Integer, ForeignKey("partes_diarios.id"), nullable=False)
    categoria = Column(String, nullable=False)          # Ej: "Oficial Armador", "Peón"
    cuadrilla_subcontrato = Column(String, nullable=True)# Ej: "Propio", "Subcontrata Estructuras"
    cantidad_operarios = Column(Integer, nullable=False)# Ej: 8
    horas_hombre = Column(Float, nullable=False)        # Ej: 64.0 (8 op x 8 hs)

    # Relación inversa hacia el parte diario
    parte_diario = relationship("ParteDiarioModel", back_populates="personal")


# ==========================================
# TABLA SECUNDARIA 3: EQUIPOS Y MAQUINARIA
# ==========================================
class MaquinariaModel(Base):
    __tablename__ = "parte_maquinaria"

    id = Column(Integer, primary_key=True, index=True)
    parte_diario_id = Column(Integer, ForeignKey("partes_diarios.id"), nullable=False)
    equipo = Column(String, nullable=False)             # Ej: "Excavadora Caterpillar 320"
    horas_operativas = Column(Float, nullable=False)    # Ej: 6.5
    horas_standby = Column(Float, default=0.0)          # Ej: 1.5 (parada por interferencia/lluvia)
    combustible_litros = Column(Float, default=0.0)     # Ej: 80.0

    # Relación inversa hacia el parte diario
    parte_diario = relationship("ParteDiarioModel", back_populates="maquinaria")