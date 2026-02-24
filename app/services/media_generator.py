"""Generación de imágenes y videos con fal.ai."""
import os
from decimal import Decimal

try:
    import fal_client
except ImportError:
    fal_client = None


def generar_imagen(prompt: str, modelo: str = None, image_urls: list = None) -> tuple[str, Decimal, str]:
    """
    Genera una imagen con fal.ai.
    - Si image_urls está vacío/None: text-to-image (Flux).
    - Si image_urls tiene URLs: image-to-image / editar (Flux 2 Edit).
    Retorna (url_imagen, costo_usd, modelo).
    """
    if not fal_client:
        raise ValueError("fal-client no instalado")
    if not os.environ.get("FAL_KEY"):
        raise ValueError("FAL_KEY no configurada. Añádela en Render Environment.")

    from app.services.modelo_config import get_modelo_default
    if not modelo:
        modelo = get_modelo_default("imagen_editar") if image_urls else get_modelo_default("imagen")

    args = {"prompt": prompt}
    if image_urls and len(image_urls) > 0:
        args["image_urls"] = image_urls[:4]  # Flux edit soporta hasta 4

    result = fal_client.run(modelo, arguments=args)

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
    return url or "", costo, modelo


def generar_video(
    prompt: str,
    image_url: str = None,
    tail_image_url: str = None,
    duration: int = 5,
    modelo_t2v: str = None,
    modelo_i2v: str = None,
) -> tuple[str, Decimal, str]:
    """
    Genera un video con fal.ai.
    - image_url: imagen de inicio (si hay → image-to-video con Kling)
    - tail_image_url: imagen de fin (solo Kling)
    - duration: segundos (5–20 según modelo; Kling Pro: 5 o 10)
    Retorna (url_video, costo_usd, modelo).
    Usa subscribe() para video (cola) con timeout 300s; run() puede fallar por timeout.
    """
    if not fal_client:
        raise ValueError("fal-client no instalado")
    if not os.environ.get("FAL_KEY"):
        raise ValueError("FAL_KEY no configurada. Añádela en Render Environment.")

    if not modelo_t2v or not modelo_i2v:
        from app.services.modelo_config import get_modelo_default
        if not modelo_t2v:
            modelo_t2v = get_modelo_default("video_t2v")
        if not modelo_i2v:
            modelo_i2v = get_modelo_default("video_i2v")

    # Text-to-video: LTX (sin image_url). Image-to-video: Kling (requiere image_url)
    has_image = image_url and str(image_url).strip()
    model = modelo_i2v if has_image else modelo_t2v

    args = {"prompt": prompt}
    if has_image:
        args["image_url"] = image_url.strip()
    if tail_image_url and str(tail_image_url).strip():
        args["tail_image_url"] = tail_image_url.strip()
    # Duración: Kling Pro solo acepta "5" o "10"
    dur = max(5, min(20, int(duration) if duration else 5))
    if "kling" in model.lower():
        args["duration"] = str(10 if dur >= 10 else 5)

    # Video usa cola; subscribe espera el resultado (run puede hacer timeout)
    try:
        result = fal_client.subscribe(
            model,
            arguments=args,
            client_timeout=300,
        )
    except ValueError:
        raise
    except Exception as e:
        err = str(e)
        if "timeout" in err.lower() or "timed out" in err.lower():
            raise ValueError("La generación de video tardó demasiado. Intenta con un prompt más corto o usa imagen de inicio.")
        if "image_url" in err.lower() and "required" in err.lower():
            raise ValueError("Para imagen→video necesitas subir una imagen de inicio.")
        raise ValueError(f"Error fal.ai: {err}")

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
    return url or "", costo, model


def submit_video(
    prompt: str,
    image_url: str = None,
    tail_image_url: str = None,
    duration: int = 5,
    modelo_t2v: str = None,
    modelo_i2v: str = None,
) -> tuple[str, str]:
    """
    Envía un video a la cola de fal.ai. Retorna (request_id, model).
    El cliente hace polling a /generaciones/:gid/result para obtener el resultado.
    Evita timeout de Render (video tarda 60-120s).
    """
    if not fal_client:
        raise ValueError("fal-client no instalado")
    if not os.environ.get("FAL_KEY"):
        raise ValueError("FAL_KEY no configurada. Añádela en Render Environment.")

    if not modelo_t2v or not modelo_i2v:
        from app.services.modelo_config import get_modelo_default
        if not modelo_t2v:
            modelo_t2v = get_modelo_default("video_t2v")
        if not modelo_i2v:
            modelo_i2v = get_modelo_default("video_i2v")

    has_image = image_url and str(image_url).strip()
    model = modelo_i2v if has_image else modelo_t2v
    args = {"prompt": prompt}
    if has_image:
        args["image_url"] = image_url.strip()
    if tail_image_url and str(tail_image_url).strip():
        args["tail_image_url"] = tail_image_url.strip()
    dur = max(5, min(20, int(duration) if duration else 5))
    if "kling" in model.lower():
        args["duration"] = str(10 if dur >= 10 else 5)

    try:
        handle = fal_client.submit(model, arguments=args)
        return handle.request_id, model
    except Exception as e:
        err = str(e)
        if "image_url" in err.lower() and "required" in err.lower():
            raise ValueError("Para imagen→video necesitas subir una imagen de inicio.")
        raise ValueError(f"Error fal.ai: {err}")


def obtener_resultado_video(request_id: str, model: str):
    """
    Obtiene el resultado de un video enviado con submit_video.
    Retorna (url, costo, model) si está listo, None si aún procesando.
    """
    if not fal_client:
        return None
    try:
        status = fal_client.status(model, request_id)
        if getattr(status, "status", str(status)) != "COMPLETED":
            return None
        result = fal_client.result(model, request_id)
    except Exception:
        return None
    url = None
    if isinstance(result, dict):
        data = result.get("response", result)
        if isinstance(data, dict):
            if "video" in data:
                v = data["video"]
                url = v.get("url") if isinstance(v, dict) else str(v)
            elif "video_url" in data:
                url = data["video_url"]
            elif "url" in data:
                url = data["url"]
        if not url and "video" in result:
            v = result["video"]
            url = v.get("url") if isinstance(v, dict) else str(v)
        elif not url and "video_url" in result:
            url = result["video_url"]
        elif not url and "url" in result:
            url = result["url"]
    costo = _extraer_costo_fal(result)
    return url or "", costo, model


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
