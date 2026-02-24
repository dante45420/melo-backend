"""Generación de prompts con OpenRouter.

Flujo conversacional:
1. Primera llamada (sin messages): la IA hace preguntas para entender mejor.
2. El usuario responde en lenguaje natural vía chat.
3. Cuando el usuario pide el prompt final: la IA entrega el prompt optimizado.
"""
import os
import json
from openai import OpenAI
from decimal import Decimal


def generar_prompt(
    cliente,
    tipo: str,
    contexto: str = None,
    modelo: str = None,
    messages: list = None,
    solicitar_prompt_final: bool = False,
    ver_estructura: bool = False,
):
    """
    Genera un prompt optimizado para imagen/video usando OpenRouter.
    Flujo conversacional: la IA hace preguntas, el usuario responde, luego pide el prompt final.

    - messages: historial de chat [{role, content}, ...]. Si vacío/None, la IA empieza con preguntas.
    - solicitar_prompt_final: si True, la IA debe entregar el prompt final (no más preguntas).

    Retorna (contenido, costo, modelo) o si ver_estructura: (contenido, costo, modelo, estructura_dict).
    """
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no configurada. Añádela en Render Environment.")

    if not modelo:
        from app.services.modelo_config import get_modelo_default
        modelo = get_modelo_default("prompt")

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
        perfil += f"\nContexto adicional: {contexto}"

    system_prompt = """Eres un experto en crear prompts para generación de imágenes y videos con IA (Flux, Kling).
Tu tarea es ayudar al usuario a refinar su idea mediante preguntas, y al final entregar un prompt optimizado.

FLUJO:
1. Si el usuario pide un prompt para imagen/video y NO hay mensajes previos: responde con 2-4 preguntas claras en español para entender mejor (qué escena, estilo visual, iluminación, mood, colores, texto a incluir, etc.). No generes el prompt aún.
2. Si hay mensajes previos y el usuario responde: haz más preguntas si falta información, o confirma que tienes suficiente.
3. Si el usuario indica que quiere el prompt final (o dice "genera el prompt", "ya está", "listo", etc.): entrega ÚNICAMENTE el prompt en inglés, optimizado para Flux/Kling. Sin explicaciones ni texto adicional. Incluye: escena, estilo, iluminación, composición, mood, y detalles que mejoren el resultado."""

    # Construir mensajes para la API
    msgs = [{"role": "system", "content": system_prompt}]

    if messages and len(messages) > 0:
        # Continuar conversación existente
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "").strip()
            if content:
                msgs.append({"role": role, "content": content})
        if solicitar_prompt_final:
            msgs.append({
                "role": "user",
                "content": "Ya tengo suficiente información. Genera ahora el prompt final en inglés, optimizado para Flux/Kling. Responde ÚNICAMENTE con el prompt, sin explicaciones."
            })
    else:
        # Primera llamada: pedir prompt + perfil → IA hace preguntas
        instruccion = f"Quiero generar un prompt para un {tipo} de marketing digital."
        msgs.append({
            "role": "user",
            "content": f"{instruccion}\n\nPerfil del cliente:\n{perfil}"
        })

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model=modelo,
            messages=msgs,
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
        usage = response.usage
        if hasattr(usage, 'total_cost') and usage.total_cost is not None:
            costo = Decimal(str(usage.total_cost))

    if ver_estructura:
        estructura = {
            "modelo": modelo,
            "perfil_cliente": perfil,
            "system_prompt": system_prompt,
            "messages": msgs,
        }
        return contenido, costo, modelo, estructura
    return contenido, costo, modelo
