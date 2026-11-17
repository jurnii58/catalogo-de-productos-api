"""Página HTML del catálogo: lista + formulario de alta."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from ..repository import SkuDuplicado
from ..repository_sql import SqlProductoRepository, get_repo
from ..schemas import Categoria, ProductoIn
from ..storage import TAMANO_MAXIMO, detectar_tipo, get_upload_dir

router = APIRouter(prefix="/web", include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

Repo = Annotated[SqlProductoRepository, Depends(get_repo)]


def _pagina(request: Request, repo: SqlProductoRepository, datos, errores, status_code=200):
    contexto = {
        "productos": repo.list(),
        "categorias": list(Categoria),
        "datos": datos,
        "errores": errores,
    }
    return templates.TemplateResponse(request, "catalogo.html", contexto, status_code=status_code)


@router.get("/productos", response_class=HTMLResponse)
def catalogo(request: Request, repo: Repo):
    return _pagina(request, repo, datos={}, errores={})


@router.post("/productos", response_class=HTMLResponse)
def agregar_desde_formulario(
    request: Request,
    repo: Repo,
    sku: Annotated[str, Form()] = "",
    nombre: Annotated[str, Form()] = "",
    precio: Annotated[str, Form()] = "",
    existencias: Annotated[str, Form()] = "",
    categoria: Annotated[str, Form()] = "",
):
    datos = {
        "sku": sku,
        "nombre": nombre,
        "precio": precio,
        "existencias": existencias,
        "categoria": categoria,
    }
    try:
        producto = ProductoIn(**datos)
    except ValidationError as error:
        errores = {e["loc"][0]: e["msg"] for e in error.errors()}
        return _pagina(request, repo, datos, errores, status_code=422)
    try:
        repo.add(producto)
    except SkuDuplicado:
        errores = {"general": "El SKU ya existe"}
        return _pagina(request, repo, datos, errores, status_code=409)
    return RedirectResponse("/web/productos", status_code=303)


@router.post("/productos/{producto_id}/imagen")
async def subir_imagen_desde_catalogo(
    producto_id: int,
    archivo: UploadFile,
    repo: Repo,
    carpeta: Annotated[Path, Depends(get_upload_dir)],
):
    if repo.get(producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="La imagen es demasiado grande")

    tipo = detectar_tipo(contenido)
    if tipo is None:
        raise HTTPException(status_code=415, detail="Tipo de archivo no soportado")

    _, extension = tipo
    ruta = carpeta / f"{uuid4().hex}{extension}"
    ruta.write_bytes(contenido)
    repo.guardar_imagen(producto_id, str(ruta))
    return RedirectResponse("/web/productos", status_code=303)
