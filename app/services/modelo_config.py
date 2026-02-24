"""Obtiene el modelo por defecto desde la BD."""
from app.models import ModeloDefault

_FALLBACK = {
    "prompt": "openai/gpt-4o-mini",
    "imagen": "fal-ai/flux/dev",
    "video_t2v": "fal-ai/ltx-video",
    "video_i2v": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
}


def get_modelo_default(clave: str) -> str:
    """Obtiene el modelo por defecto para la clave dada."""
    md = ModeloDefault.query.filter_by(clave=clave).first()
    if md and md.modelo:
        return md.modelo
    return _FALLBACK.get(clave, "")
