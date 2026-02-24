"""Rutas para configuración de modelos y listado de modelos disponibles."""
import os
import requests
from flask import Blueprint, request, jsonify
from app import db
from app.models import ModeloDefault

bp = Blueprint("modelos", __name__, url_prefix="/api/modelos")


def _get_default(clave: str) -> str:
    """Obtiene el modelo por defecto desde BD."""
    md = ModeloDefault.query.filter_by(clave=clave).first()
    return md.modelo if md else ""


@bp.route("/default", methods=["GET"])
def obtener_default():
    """Devuelve los modelos por defecto actuales."""
    defaults = {}
    for clave in ("prompt", "imagen", "video_t2v", "video_i2v"):
        defaults[clave] = _get_default(clave)
    # Valores fallback si no existen en BD
    fallback = {
        "prompt": "openai/gpt-4o-mini",
        "imagen": "fal-ai/flux/dev",
        "video_t2v": "fal-ai/ltx-video",
        "video_i2v": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
    }
    for k, v in fallback.items():
        if not defaults.get(k):
            defaults[k] = v
    return jsonify(defaults)


@bp.route("/default", methods=["PUT"])
def actualizar_default():
    """Actualiza los modelos por defecto."""
    data = request.get_json() or {}
    for clave, modelo in data.items():
        if clave not in ("prompt", "imagen", "video_t2v", "video_i2v"):
            continue
        modelo_str = (modelo or "").strip()
        if not modelo_str:
            continue
        md = ModeloDefault.query.filter_by(clave=clave).first()
        if md:
            md.modelo = modelo_str
        else:
            md = ModeloDefault(clave=clave, modelo=modelo_str)
            db.session.add(md)
    db.session.commit()
    return obtener_default()


@bp.route("/openrouter", methods=["GET"])
def listar_openrouter():
    """Lista modelos disponibles en OpenRouter (proxy para evitar CORS en cliente)."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENROUTER_API_KEY no configurada", "models": []}), 200
    try:
        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        models = data.get("data", [])
        # Filtrar solo modelos de texto (para prompts), no imagen/audio
        out = []
        for m in models:
            mid = m.get("id")
            name = m.get("name", mid)
            if mid and name:
                out.append({"id": mid, "name": name})
        return jsonify({"models": out[:150]})  # límite razonable
    except requests.RequestException as e:
        print(f"[Melo] OpenRouter models error: {e}", flush=True)
        return jsonify({"error": str(e), "models": []}), 200


@bp.route("/fal", methods=["GET"])
def listar_fal():
    """Lista modelos disponibles en fal.ai por categoría."""
    category = request.args.get("category", "text-to-image")
    # Categorías válidas: text-to-image, text-to-video, image-to-video
    valid = ("text-to-image", "text-to-video", "image-to-video")
    if category not in valid:
        category = "text-to-image"
    api_key = os.environ.get("FAL_KEY", "")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Key {api_key}"
    try:
        r = requests.get(
            "https://api.fal.ai/v1/models",
            params={"category": category, "status": "active", "limit": 100},
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        models = data.get("models", [])
        out = []
        for m in models:
            eid = m.get("endpoint_id")
            meta = m.get("metadata", {}) or {}
            name = meta.get("display_name", eid or "")
            if eid:
                out.append({"id": eid, "name": name or eid})
        return jsonify({"models": out})
    except requests.RequestException as e:
        print(f"[Melo] fal models error: {e}", flush=True)
        return jsonify({"error": str(e), "models": []}), 200
