from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cadena de conexión con comillas y sin corchetes en la contraseña
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.rvruadjhosplxjzyruca:2354MonteVIdeo43@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
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