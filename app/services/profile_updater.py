"""Actualización del perfil del cliente basada en feedback."""
import os
import json
from openai import OpenAI


def extraer_insights_de_feedback(contenido_feedback: str, perfil_actual: dict) -> dict:
    """
    Usa OpenRouter para extraer insights del feedback y devolver
    un dict con campos a actualizar (tono_voz, colores_preferidos, etc.)
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {}

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    system = """Eres un asistente que analiza feedback de clientes sobre contenido de marketing.
Dado el feedback y el perfil actual, extrae insights concretos y devuelve JSON con solo los campos que deben actualizarse.
Campos posibles: tono_voz, colores_preferidos, referencias_visuales (array de strings).
Responde ÚNICAMENTE con JSON válido, sin texto adicional. Ejemplo: {"tono_voz": "más formal", "colores_preferidos": "evitar rojo"}"""

    user = f"""Feedback del cliente:
"{contenido_feedback}"

Perfil actual: {json.dumps(perfil_actual)}

Devuelve solo el JSON con los campos a actualizar (solo los que apliquen):"""

    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        return {}
