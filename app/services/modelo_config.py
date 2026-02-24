"""Obtiene el modelo por defecto desde la BD.

Los modelos que seleccionas en la página Modelos se guardan en la tabla ModeloDefault
y se usan aquí. _FALLBACK solo se usa cuando no hay fila en BD para esa clave
(ej. antes de ejecutar el seed o si la clave no existe).
"""
from app.models import ModeloDefault

_FALLBACK = {
    "prompt": "openai/gpt-4o-mini",
    "imagen": "fal-ai/flux/dev",
    "imagen_editar": "fal-ai/flux-2/turbo/edit",
    "video_t2v": "fal-ai/ltx-video",
    "video_i2v": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
}


def get_modelo_default(clave: str) -> str:
    """Obtiene el modelo por defecto para la clave dada."""
    md = ModeloDefault.query.filter_by(clave=clave).first()
    if md and md.modelo:
        return md.modelo
    return _FALLBACK.get(clave, "")
