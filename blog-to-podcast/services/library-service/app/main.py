from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas, database
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Library Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "library-service"}

@app.post("/podcasts", response_model=schemas.Podcast)
def create_podcast(podcast: schemas.PodcastCreate, db: Session = Depends(get_db)):
    db_podcast = models.Podcast(**podcast.dict())
    db.add(db_podcast)
    db.commit()
    db.refresh(db_podcast)
    return db_podcast

@app.get("/podcasts", response_model=List[schemas.Podcast])
def read_podcasts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    podcasts = db.query(models.Podcast).offset(skip).limit(limit).all()
    return podcasts

@app.get("/podcasts/{podcast_id}", response_model=schemas.Podcast)
def read_podcast(podcast_id: int, db: Session = Depends(get_db)):
    db_podcast = db.query(models.Podcast).filter(models.Podcast.id == podcast_id).first()
    if db_podcast is None:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return db_podcast

@app.delete("/podcasts/{podcast_id}")
def delete_podcast(podcast_id: int, db: Session = Depends(get_db)):
    db_podcast = db.query(models.Podcast).filter(models.Podcast.id == podcast_id).first()
    if db_podcast is None:
        raise HTTPException(status_code=404, detail="Podcast not found")
    db.delete(db_podcast)
    db.commit()
    return {"message": "Podcast deleted"}
