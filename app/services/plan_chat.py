"""Chat guiado para crear el plan de marketing.

La IA actúa como un empleado de marketing profesional, hace preguntas
y genera un plan estructurado con objetivos, campañas y métricas.
"""
import os
import json
import uuid
from openai import OpenAI


def _plan_inicial():
    return {
        "objetivos": [],
        "campañas": [],
    }


def obtener_plan(cliente):
    """Obtiene el plan del cliente o uno vacío."""
    if getattr(cliente, "plan_marketing", None) and isinstance(cliente.plan_marketing, dict):
        return cliente.plan_marketing
    return _plan_inicial()


def chat_plan(cliente, user_message: str, messages: list, guardar: bool = False):
    """
    Responde en el chat de creación de plan de marketing.
    Si guardar=True, extrae y retorna el plan en JSON.
    Retorna: (respuesta_ia, plan_o_none)
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no configurada")

    from app.services.contexto_chat import obtener_contexto
    contexto = obtener_contexto(cliente)
    plan_actual = obtener_plan(cliente)
    info = contexto.get("informacion_empresa") or {}
    empresa = info.get("empresa") or cliente.empresa or "la empresa"
    industria = info.get("industria") or cliente.industria or ""

    system_prompt = f"""Eres un profesional de marketing experimentado que ayuda a crear planes de marketing.
Estás conversando con el dueño de {empresa} ({industria}).

Plan actual (si existe):
{json.dumps(plan_actual, ensure_ascii=False, indent=2)}

COMPORTAMIENTO:
1. Actúa como un empleado de marketing profesional. Haz preguntas claras y específicas.
2. Primera interacción sin historial: haz 3-5 preguntas profesionales como:
   - "¿Cuáles son tus objetivos principales para este trimestre/semestre? (ej: aumentar ventas 20%, ganar 500 seguidores)"
   - "¿Qué canales usas o quieres priorizar? (Instagram, TikTok, Facebook, WhatsApp, email, etc.)"
   - "¿Tienes fechas clave o campañas planeadas? (Black Friday, lanzamiento producto, temporada)"
   - "¿Cómo medirás el éxito? (impresiones, engagement, conversiones, ventas)"
   - "¿Cuál es tu presupuesto aproximado para marketing/ads?"
3. Con las respuestas, construye gradualmente el plan. Pide aclaraciones si falta información.
4. Si el usuario pide "ver el plan" o "ver resumen": muéstralo por secciones de forma legible.
5. Si guardar=True: genera el plan final en JSON con esta estructura EXACTA:

{{
  "objetivos": [
    {{ "id": "uuid", "nombre": "string", "meta": "string", "actual": "", "progreso": 0, "estado": "en_progreso" }}
  ],
  "campañas": [
    {{
      "id": "uuid",
      "nombre": "string",
      "objetivo_id": "id del objetivo",
      "fecha_inicio": "YYYY-MM",
      "fecha_fin": "YYYY-MM",
      "canales": ["Instagram", "TikTok"],
      "metricas": {{ "impresiones": {{ "meta": 10000, "actual": 0 }}, "engagement": {{ "meta": 5, "actual": 0 }}, "conversiones": {{ "meta": 50, "actual": 0 }} }},
      "estado": "activa"
    }}
  ]
}}

- Usa uuid v4 para ids (puedes usar valores cortos como "obj1", "camp1").
- metricas: incluir solo las que apliquen. Valores numéricos para meta y actual.
- estado en objetivos: en_progreso | cumplido | atrasado
- estado en campañas: planificada | activa | finalizada
6. NUNCA inventes datos. Si falta algo crítico, pregúntalo antes de guardar."""

    if guardar:
        system_prompt += """

IMPORTANTE: Cuando el usuario pida guardar, tu respuesta debe incluir un bloque de código JSON (entre ```json y ```) con el plan completo. No incluyas otro texto después del JSON."""

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

    plan = None
    if guardar:
        if "```json" in contenido:
            try:
                inicio = contenido.find("```json") + 7
                fin = contenido.find("```", inicio)
                if fin > inicio:
                    plan = json.loads(contenido[inicio:fin].strip())
            except json.JSONDecodeError:
                pass
        if plan is None and "```" in contenido:
            try:
                inicio = contenido.find("```") + 3
                fin = contenido.find("```", inicio)
                if fin > inicio:
                    plan = json.loads(contenido[inicio:fin].strip())
            except json.JSONDecodeError:
                pass
        if plan is None and contenido.strip().startswith("{"):
            try:
                plan = json.loads(contenido.strip())
            except json.JSONDecodeError:
                pass

        if plan:
            # Normalizar: asegurar objetivos y campañas con ids
            if "objetivos" not in plan:
                plan["objetivos"] = []
            if "campañas" not in plan:
                plan["campañas"] = []
            for o in plan["objetivos"]:
                if not o.get("id"):
                    o["id"] = str(uuid.uuid4())[:8]
                o.setdefault("estado", "en_progreso")
                o.setdefault("progreso", 0)
            for c in plan["campañas"]:
                if not c.get("id"):
                    c["id"] = str(uuid.uuid4())[:8]
                c.setdefault("estado", "activa")
                c.setdefault("metricas", {})

    return contenido, plan


def build_contexto_para_prompt(cliente, campaña_id=None):
    """Construye el string de contexto completo (perfil + plan) para generar prompts.
    Incluye toda la info de la empresa y el plan para que la IA genere contenido alineado."""
    from app.services.contexto_chat import obtener_contexto
    ctx = obtener_contexto(cliente)
    plan = obtener_plan(cliente)

    parts = [
        "CONTEXTO COMPLETO PARA GENERAR CONTENIDO:",
        "",
        "--- EMPRESA ---",
        f"Empresa: {ctx.get('informacion_empresa', {}).get('empresa') or cliente.empresa}",
        f"Industria: {ctx.get('informacion_empresa', {}).get('industria') or cliente.industria}",
        f"Descripción: {ctx.get('informacion_empresa', {}).get('descripcion') or cliente.descripcion_negocio}",
        "",
        "--- ESTILO ---",
        f"Tono: {ctx.get('estilo_empresa', {}).get('tono_voz') or cliente.tono_voz}",
        f"Colores: {ctx.get('estilo_empresa', {}).get('colores_preferidos') or cliente.colores_preferidos}",
        "",
    ]
    pub = ctx.get("publico_objetivo") or {}
    if pub.get("descripcion"):
        parts.append(f"Público objetivo: {pub['descripcion']}")
    obj = ctx.get("objetivos_marketing") or {}
    if obj.get("descripcion"):
        parts.append(f"Objetivos: {obj['descripcion']}")

    parts.append("")
    parts.append("--- PLAN DE MARKETING ACTUAL ---")
    for o in plan.get("objetivos", []):
        parts.append(f"Objetivo: {o.get('nombre')} | Meta: {o.get('meta')} | Estado: {o.get('estado')}")
    for c in plan.get("campañas", []):
        if campaña_id and c.get("id") != campaña_id:
            continue
        parts.append(f"Campaña: {c.get('nombre')} ({c.get('fecha_inicio')} a {c.get('fecha_fin')})")
        parts.append(f"  Canales: {', '.join(c.get('canales', []))}")
        parts.append(f"  Estado: {c.get('estado')}")

    return "\n".join(parts)
