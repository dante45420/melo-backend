"""Añade texto sobreimpreso a un video usando FFmpeg.

Descarga el video, aplica drawtext, sube el resultado a fal.ai.
"""
import os
import tempfile
import subprocess
import requests


def _get_ffmpeg_path():
    """Obtiene la ruta al binario ffmpeg (imageio-ffmpeg)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def agregar_texto_video(video_url: str, texto: str, posicion: str = "center") -> str:
    """
    Descarga el video, añade el texto con FFmpeg, sube a fal.ai.
    Retorna la nueva URL del video con texto.

    posicion: 'center', 'top', 'bottom'
    """
    if not texto or not texto.strip():
        raise ValueError("El texto no puede estar vacío")

    texto = texto.strip()
    ffmpeg = _get_ffmpeg_path()

    # Escapar comillas para drawtext (FFmpeg requiere escapar '\' y ':')
    # drawtext usa: text='texto' - las comillas simples protegen
    texto_esc = texto.replace("'", "'\\''").replace(":", "\\:").replace("%", "\\%")

    # Posición Y según opción
    if posicion == "top":
        y = 80
    elif posicion == "bottom":
        y = "h-th-80"
    else:
        y = "(h-th)/2"

    # drawtext: texto centrado, blanco con borde negro (legible sobre cualquier fondo)
    vf = f"drawtext=text='{texto_esc}':fontsize=48:fontcolor=white:bordercolor=black:borderw=2:x=(w-text_w)/2:y={y}"

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "output.mp4")

        # Descargar video
        r = requests.get(video_url, stream=True, timeout=60)
        r.raise_for_status()
        with open(input_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # FFmpeg
        cmd = [
            ffmpeg, "-y", "-i", input_path,
            "-vf", vf,
            "-c:a", "copy",
            "-movflags", "+faststart",
            output_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise ValueError(f"FFmpeg error: {proc.stderr[:500] if proc.stderr else 'unknown'}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise ValueError("FFmpeg no generó archivo válido")

        # Subir a fal
        import fal_client
        if not os.environ.get("FAL_KEY"):
            raise ValueError("FAL_KEY no configurada")
        url = fal_client.upload_file(output_path)
        return url
