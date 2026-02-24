"""Generación de prompts con OpenRouter."""
import os
import json
import requests
from openai import OpenAI
from decimal import Decimal


def generar_prompt(cliente, tipo: str, contexto: str = None) -> tuple[str, Decimal | None]:
    """
    Genera un prompt optimizado para imagen/video usando OpenRouter.
    Retorna (contenido_prompt, costo_usd).
    """
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no configurada. Añádela en Render Environment.")

    # Construir contexto del perfil
    perfil = f"""
Cliente: {cliente.nombre}
Empresa: {cliente.empresa or 'N/A'}
Industria: {cliente.industria or 'N/A'}
Descripción del negocio: {cliente.descripcion_negocio or 'N/A'}
Tono de voz deseado: {cliente.tono_voz or 'profesional'}
Colores preferidos: {cliente.colores_preferidos or 'N/A'}
Referencias visuales: {json.dumps(cliente.referencias_visuales or [])}
"""
    if contexto:
        perfil += f"\nContexto adicional para esta generación: {contexto}"

    system_prompt = """Eres un experto en crear prompts para generación de imágenes y videos con IA.
Tu tarea es crear un prompt detallado, en inglés, optimizado para que modelos como Flux o Kling generen contenido de alta calidad para marketing.
Incluye: escena, estilo visual, iluminación, composición, mood, y cualquier detalle que mejore el resultado.
Responde ÚNICAMENTE con el prompt, sin explicaciones ni texto adicional."""

    user_message = f"Genera un prompt para un {tipo} de marketing digital.\n\nPerfil del cliente:\n{perfil}"

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "authentication" in err_msg.lower():
            raise ValueError("OpenRouter: API key inválida o expirada")
        if "429" in err_msg or "rate" in err_msg.lower():
            raise ValueError("OpenRouter: límite de uso alcanzado, intenta más tarde")
        raise

    if not response.choices or len(response.choices) == 0:
        raise ValueError("OpenRouter no devolvió respuesta. Reintenta.")
    contenido = response.choices[0].message.content.strip()
    costo = None
    if hasattr(response, 'usage') and response.usage:
        # OpenRouter devuelve usage; algunos modelos incluyen total_cost
        usage = response.usage
        if hasattr(usage, 'total_cost') and usage.total_cost is not None:
            costo = Decimal(str(usage.total_cost))
        # Alternativa: algunos endpoints devuelven cost en otro formato
        # Por ahora usamos 0 si no hay dato explícito (OpenRouter puede variar)

    return contenido, costo
