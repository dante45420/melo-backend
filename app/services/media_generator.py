"""Generación de imágenes y videos con fal.ai."""
import os
from decimal import Decimal

try:
    import fal_client
except ImportError:
    fal_client = None


# Modelos fal.ai (ver https://fal.ai/models)
FAL_MODEL_IMAGEN = "fal-ai/flux/dev"
FAL_MODEL_VIDEO_T2V = "fal-ai/ltx-video"  # text-to-video (preview) o fal-ai/ltxv-2/text-to-video/fast
FAL_MODEL_VIDEO_I2V = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"  # image-to-video


def generar_imagen(prompt: str) -> tuple[str, Decimal]:
    """
    Genera una imagen con fal.ai Flux.
    Retorna (url_imagen, costo_usd).
    """
    if not fal_client:
        raise ValueError("fal-client no instalado")
    key = os.environ.get("FAL_KEY")
    if not key:
        raise ValueError("FAL_KEY no configurada")

    result = fal_client.run(FAL_MODEL_IMAGEN, arguments={"prompt": prompt})

    url = None
    if isinstance(result, dict):
        if "images" in result and result["images"]:
            img = result["images"][0]
            url = img.get("url") if isinstance(img, dict) else str(img)
        elif "image" in result:
            url = result["image"].get("url") if isinstance(result["image"], dict) else str(result["image"])
        elif "url" in result:
            url = result["url"]

    costo = _extraer_costo_fal(result)
    return url or "", costo


def generar_video(prompt: str, image_url: str = None) -> tuple[str, Decimal]:
    """
    Genera un video con fal.ai.
    Si image_url se proporciona, usa image-to-video (Kling); si no, text-to-video (LTX).
    Retorna (url_video, costo_usd).
    """
    if not fal_client:
        raise ValueError("fal-client no instalado")
    key = os.environ.get("FAL_KEY")
    if not key:
        raise ValueError("FAL_KEY no configurada")

    model = FAL_MODEL_VIDEO_I2V if image_url else FAL_MODEL_VIDEO_T2V
    args = {"prompt": prompt}
    if image_url:
        args["image_url"] = image_url

    result = fal_client.run(model, arguments=args)

    url = None
    if isinstance(result, dict):
        if "video" in result:
            v = result["video"]
            url = v.get("url") if isinstance(v, dict) else str(v)
        elif "video_url" in result:
            url = result["video_url"]
        elif "url" in result:
            url = result["url"]

    costo = _extraer_costo_fal(result)
    return url or "", costo


def _extraer_costo_fal(result: dict) -> Decimal:
    """
    Extrae el costo de la respuesta de fal.ai.
    fal.ai puede incluir 'timing' o 'cost' en la respuesta.
    Si no está disponible, usar Usage API: GET https://api.fal.ai/v1/models/usage
    """
    if not isinstance(result, dict):
        return Decimal("0")
    if "cost" in result and result["cost"] is not None:
        try:
            return Decimal(str(result["cost"]))
        except Exception:
            pass
    if "timing" in result and isinstance(result["timing"], dict):
        # Algunos modelos devuelven cost en timing
        t = result["timing"]
        if "total_cost" in t:
            try:
                return Decimal(str(t["total_cost"]))
            except Exception:
                pass
    # Sin costo explícito: usar estimación o 0. Consultar Usage API para valores exactos.
    return Decimal("0")
