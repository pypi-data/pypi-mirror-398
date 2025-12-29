from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from kryten_playlist.web.deps import get_current_session, get_kv

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

router = APIRouter()


def _ctx(request: Request, **extra: Any) -> dict[str, Any]:
    ctx: dict[str, Any] = {"request": request}
    ctx.update(extra)
    return ctx


async def _is_authed(request: Request) -> bool:
    if not request.cookies.get("kryten_playlist_session"):
        return False
    try:
        kv = get_kv(request)
        await get_current_session(request, kv)
        return True
    except Exception:
        return False


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if await _is_authed(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", _ctx(request))


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    if not await _is_authed(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("index.html", _ctx(request))


@router.get("/playlists", response_class=HTMLResponse)
async def playlists_page(request: Request):
    if not await _is_authed(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("playlists.html", _ctx(request))


@router.get("/playlists/{playlist_id}", response_class=HTMLResponse)
async def playlist_editor_page(request: Request, playlist_id: str):
    if not await _is_authed(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("playlist_editor.html", _ctx(request, playlist_id=playlist_id))


@router.get("/apply", response_class=HTMLResponse)
async def apply_page(request: Request):
    if not await _is_authed(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("apply.html", _ctx(request))


@router.get("/marathon", response_class=HTMLResponse)
async def marathon_page(request: Request):
    if not await _is_authed(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("marathon.html", _ctx(request))


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    if not await _is_authed(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("stats.html", _ctx(request))
