"""Pruebas del flujo de carga de imágenes desde el catálogo web."""


def test_subir_imagen_desde_catalogo(client):
    client.post(
        "/productos",
        json={
            "sku": "TEC-001",
            "nombre": "Teclado",
            "precio": 899,
            "existencias": 10,
            "categoria": "perifericos",
        },
    )
    contenido = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

    respuesta = client.post(
        "/web/productos/1/imagen",
        files={"archivo": ("teclado.png", contenido, "image/png")},
        follow_redirects=False,
    )

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/web/productos"
    assert client.get("/productos/1/imagen").content == contenido
