from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel

class Song(BaseModel):
    id: str
    title: str
    artist: str

app = FastAPI()

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory playlist
playlist = []

@app.get("/", response_class=HTMLResponse)
async def read_playlist(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "playlist": playlist})

@app.post("/add")
async def add_song(title: str = Form(...), artist: str = Form(...)):
    song = Song(id=str(uuid4()), title=title, artist=artist)
    playlist.append(song)
    return RedirectResponse("/", status_code=303)

@app.post("/update")
async def update_song(id: str = Form(...), title: str = Form(...), artist: str = Form(...)):
    for song in playlist:
        if song.id == id:
            song.title = title
            song.artist = artist
            break
    return RedirectResponse("/", status_code=303)

@app.post("/delete")
async def delete_song(id: str = Form(...)):
    global playlist
    playlist = [song for song in playlist if song.id != id]
    return RedirectResponse("/", status_code=303)