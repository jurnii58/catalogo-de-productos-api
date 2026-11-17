"""Subir y ver la imagen de un producto."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..repository_sql import SqlProductoRepository, get_repo
from ..schemas import ProductoOut
from ..storage import TAMANO_MAXIMO, detectar_tipo, get_upload_dir

router = APIRouter(prefix="/productos", tags=["Imágenes"])

Repo = Annotated[SqlProductoRepository, Depends(get_repo)]
Carpeta = Annotated[Path, Depends(get_upload_dir)]


@router.post("/{producto_id}/imagen", response_model=ProductoOut)
async def subir_imagen(
    producto_id: int,
    archivo: UploadFile,
    repo: Repo,
    carpeta: Carpeta,
) -> ProductoOut:
    if repo.get(producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="La imagen es demasiado grande")

    tipo = detectar_tipo(contenido)
    if tipo is None:
        raise HTTPException(status_code=415, detail="Tipo de archivo no soportado")

    mime, extension = tipo
    nombre = f"{uuid4().hex}{extension}"
    ruta = carpeta / nombre
    ruta.write_bytes(contenido)

    producto = repo.guardar_imagen(producto_id, str(ruta))
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.get("/{producto_id}/imagen")
def ver_imagen(producto_id: int, repo: Repo) -> FileResponse:
    ruta = repo.ruta_imagen(producto_id)
    if ruta is None or not Path(ruta).exists():
        raise HTTPException(status_code=404, detail="El producto no tiene imagen")
    return FileResponse(ruta)
