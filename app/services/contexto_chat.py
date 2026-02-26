"""Chat con IA para editar el contexto/perfil del cliente por secciones.

El contexto se guarda como JSON estructurado en la BD.
Secciones: informacion_empresa, estilo_empresa, ultimos_posts, publico_objetivo, objetivos_marketing, otros.
"""
import os
import json
from openai import OpenAI

SECCIONES = [
    "informacion_empresa",
    "estilo_empresa",
    "ultimos_posts",
    "publico_objetivo",
    "objetivos_marketing",
    "otros",
]

ESQUEMA_CONTEXTO = {
    "informacion_empresa": {
        "nombre": "Información de la empresa",
        "campos": ["nombre", "empresa", "industria", "descripcion"],
    },
    "estilo_empresa": {
        "nombre": "Estilo de la empresa",
        "campos": ["tono_voz", "colores_preferidos", "referencias_visuales"],
    },
    "ultimos_posts": {
        "nombre": "Últimos 3 posts",
        "campos": ["posts"],
    },
    "publico_objetivo": {
        "nombre": "Público objetivo",
        "campos": ["descripcion"],
    },
    "objetivos_marketing": {
        "nombre": "Objetivos de marketing",
        "campos": ["descripcion"],
    },
    "otros": {
        "nombre": "Otros",
        "campos": ["notas"],
    },
}


def _contexto_inicial_desde_cliente(cliente):
    """Construye contexto inicial desde los campos legacy del cliente."""
    ctx = {
        "informacion_empresa": {
            "nombre": cliente.nombre,
            "empresa": cliente.empresa or "",
            "industria": cliente.industria or "",
            "descripcion": cliente.descripcion_negocio or "",
        },
        "estilo_empresa": {
            "tono_voz": cliente.tono_voz or "",
            "colores_preferidos": cliente.colores_preferidos or "",
            "referencias_visuales": cliente.referencias_visuales or [],
        },
        "ultimos_posts": {
            "posts": [],
        },
        "publico_objetivo": {"descripcion": ""},
        "objetivos_marketing": {"descripcion": ""},
        "otros": {"notas": ""},
    }
    if cliente.referencias_visuales and isinstance(cliente.referencias_visuales, list):
        ctx["estilo_empresa"]["referencias_visuales"] = cliente.referencias_visuales
    return ctx


def obtener_contexto(cliente):
    """Obtiene el contexto del cliente. Si no hay contexto_perfil, lo arma desde campos legacy."""
    if getattr(cliente, "contexto_perfil", None) and isinstance(cliente.contexto_perfil, dict):
        return cliente.contexto_perfil
    return _contexto_inicial_desde_cliente(cliente)


def chat_contexto(cliente, user_message: str, messages: list, guardar: bool = False):
    """
    Responde al usuario en el chat de edición de contexto.
    Si guardar=True, la IA extrae las actualizaciones y retorna un dict para guardar en contexto_perfil.
    Retorna: (respuesta_ia, actualizaciones_o_none)
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no configurada")

    contexto_actual = obtener_contexto(cliente)
    contexto_str = json.dumps(contexto_actual, ensure_ascii=False, indent=2)

    system_prompt = f"""Eres un asistente que ayuda a editar el perfil/contexto de marketing de un cliente.
El contexto actual está en JSON con estas secciones:
- informacion_empresa: nombre, empresa, industria, descripcion
- estilo_empresa: tono_voz, colores_preferidos, referencias_visuales (array)
- ultimos_posts: posts (array de {{titulo, descripcion}})
- publico_objetivo: descripcion
- objetivos_marketing: descripcion
- otros: notas

Contexto actual:
{contexto_str}

INSTRUCCIONES:
1. Responde en español, de forma amigable y conversacional.
2. Si el usuario da información nueva, confirma qué sección vas a actualizar.
3. Si el usuario pide ver el perfil: muéstralo por secciones de forma legible.
4. Si guardar=True (el usuario dice "guardar", "aplicar", "listo", etc.): responde con un JSON válido que sea el contexto actualizado completo. Ese JSON debe tener las mismas secciones que el ejemplo.
5. NUNCA inventes datos. Si falta algo, pregúntalo.
6. Para ultimos_posts, usa formato: [{{"titulo": "...", "descripcion": "..."}}, ...] hasta 3 posts."""

    if guardar:
        system_prompt += """

IMPORTANTE: Cuando el usuario pida guardar, tu ÚLTIMA respuesta debe ser un bloque de código JSON (entre ```json y ```) que contenga el contexto completo actualizado. No incluyas otro texto después del JSON."""

    from app.services.modelo_config import get_modelo_default
    modelo = get_modelo_default("prompt")

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    msgs = [{"role": "system", "content": system_prompt}]
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "").strip()
        if content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": user_message})

    resp = client.chat.completions.create(model=modelo, messages=msgs)
    contenido = resp.choices[0].message.content.strip()

    actualizaciones = None
    if guardar:
        # Intentar extraer JSON: bloque ```json, luego ```, luego JSON puro
        if "```json" in contenido:
            try:
                inicio = contenido.find("```json") + 7
                fin = contenido.find("```", inicio)
                if fin > inicio:
                    actualizaciones = json.loads(contenido[inicio:fin].strip())
            except json.JSONDecodeError:
                pass
        if actualizaciones is None and "```" in contenido:
            try:
                inicio = contenido.find("```") + 3
                fin = contenido.find("```", inicio)
                if fin > inicio:
                    actualizaciones = json.loads(contenido[inicio:fin].strip())
            except json.JSONDecodeError:
                pass
        if actualizaciones is None and contenido.strip().startswith("{"):
            try:
                actualizaciones = json.loads(contenido.strip())
            except json.JSONDecodeError:
                pass

    return contenido, actualizaciones
