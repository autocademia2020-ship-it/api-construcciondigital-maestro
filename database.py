import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Lee la variable de entorno configurada en Render (Neon)
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# Si no encuentra la variable de entorno (por si pruebas localmente), usa None
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("La variable de entorno SQLALCHEMY_DATABASE_URL no está configurada")

# Motor de conexión
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Sesión local para consultas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos de las tablas
Base = declarative_base()

# Función para obtener la sesión de BD en cada endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
