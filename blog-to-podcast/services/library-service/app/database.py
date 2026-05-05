import os
import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/library_db")

# Thêm cơ chế retry để đợi database sẵn sàng
engine = None
for i in range(10):
    try:
        engine = create_engine(DATABASE_URL)
        # Thử kết nối thực tế
        with engine.connect() as conn:
            break
    except Exception as e:
        print(f"Waiting for database... ({i+1}/10)")
        time.sleep(2)

if engine is None:
    raise Exception("Could not connect to database after several attempts")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
