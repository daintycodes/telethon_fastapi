from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Serve a minimal admin UI for approving media and managing channels."""
    return templates.TemplateResponse("admin.html", {"request": request})
