from fastapi import FastAPI, Depends, HTTPException
from fastapi import  Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Field, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from typing import Optional
from pydantic import BaseModel


DATABASE_URL = "postgresql://postgres:Sarah:11@localhost:5432/Tracks"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DATABASE_URL = "postgresql+asyncpg://postgres:Sarah:11@localhost:5432/Tracks"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Track(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    artist: str

class TrackCreate(BaseModel):
    title: str
    artist: str

# Response schema (what API returns)
class TrackRead(SQLModel):
    id: int
    title: str
    artist: str

app = FastAPI()

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async with async_session() as session:
        yield session

@app.get("/", response_class=HTMLResponse)
async def read_playlist(request: Request, session: AsyncSession = Depends(get_session)):
    results = await session.execute(select(Track))
    tracks = results.scalars().all()
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tracks/")
def read_tracks(db: Session = Depends(get_db)):
    return db.query(Track).all()

@app.post("/tracks/")
def create_track(track: TrackCreate, db: Session = Depends(get_db)):
    db_track = Track(**track.dict())
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track

@app.patch("/tracks/{track_id}", response_model=TrackRead)
async def update_track(
    track_id: int,
    track: TrackCreate,
    db: Session = Depends(get_db)
):
    db_track = db.query(Track).get(track_id)
    if not db_track:
        raise HTTPException(status_code=404, detail="Not found")
    for k,v in track.dict().items():
        setattr(db_track, k, v)
    db.commit()
    db.refresh(db_track)
    return db_track


@app.delete("/tracks/{track_id}")
async def delete_track(track_id: int, session: AsyncSession = Depends(get_session)):
    db = await session.get(Track, track_id)
    if not db:
        raise HTTPException(404, "Track not found")
    await session.delete(db)
    await session.commit()
    return {"ok": True}
