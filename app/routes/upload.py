"""Subida de archivos a fal.ai storage."""
import os
import tempfile
from flask import Blueprint, request, jsonify

bp = Blueprint("upload", __name__, url_prefix="/api")


def _upload_to_fal(file_path: str) -> str:
    """Sube un archivo a fal.ai y retorna la URL."""
    try:
        import fal_client
        if not fal_client:
            raise ValueError("fal-client no disponible")
        url = fal_client.upload_file(file_path)
        return url
    except ImportError:
        raise ValueError("fal-client no instalado")
    except Exception as e:
        raise ValueError(f"Error subiendo a fal: {str(e)}")


@bp.route("/upload", methods=["POST"])
def subir_imagenes():
    """
    Sube una o más imágenes a fal.ai storage.
    Acepta multipart/form-data con campo 'images' o 'image'.
    Retorna {"urls": ["https://...", ...]}.
    """
    if not os.environ.get("FAL_KEY"):
        return jsonify({"error": "FAL_KEY no configurada"}), 503

    files = request.files.getlist("images") or request.files.getlist("image") or []
    if not files and "image" in request.files:
        files = [request.files["image"]]

    if not files:
        return jsonify({"error": "No se enviaron imágenes. Usa el campo 'images' o 'image'"}), 400

    # Límite 8 imágenes (4 para edit + 4 para video start/end/elements)
    files = files[:8]

    urls = []
    for f in files:
        if not f or not f.filename:
            continue
        ext = os.path.splitext(f.filename)[1] or ".png"
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            continue
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp_path = tmp.name
                f.save(tmp_path)
                url = _upload_to_fal(tmp_path)
                urls.append(url)
        except Exception as e:
            print(f"[Melo] upload error: {e}", flush=True)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    if not urls:
        return jsonify({"error": "No se pudieron subir las imágenes"}), 400
    return jsonify({"urls": urls})
