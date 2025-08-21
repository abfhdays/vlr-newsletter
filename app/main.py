from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter
from app.db import engine, Base, SessionLocal
from app.gql.schema import schema
from app.services.selection import last_week

app = FastAPI(title="VLR Newsletter (Minimal)")
app.include_router(GraphQLRouter(schema), prefix="/graphql")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# auto-create tables once
Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    with SessionLocal() as db:
        arts, mats = last_week(db)
    return templates.TemplateResponse("dashboard.html", {"request": request, "articles": arts, "matches": mats})

@app.get("/preview", response_class=HTMLResponse)
def preview(request: Request):
    with SessionLocal() as db:
        arts, mats = last_week(db)
    return templates.TemplateResponse("preview.html", {"request": request, "articles": arts, "matches": mats})
