"""Rutas de clientes."""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Cliente, Prompt, Feedback, Instancia, Generacion, CreditoMovimiento, PrecioTarifa
from decimal import Decimal
from app.services.prompt_generator import generar_prompt as svc_generar_prompt
from app.services.media_generator import generar_imagen, generar_video, submit_video, obtener_resultado_video
from app.services.profile_updater import extraer_insights_de_feedback

bp = Blueprint("clientes", __name__, url_prefix="/api/clientes")


def _cliente_json(c):
    return {
        "id": c.id,
        "nombre": c.nombre,
        "empresa": c.empresa,
        "industria": c.industria,
        "descripcion_negocio": c.descripcion_negocio,
        "tono_voz": c.tono_voz,
        "colores_preferidos": c.colores_preferidos,
        "referencias_visuales": c.referencias_visuales,
        "credito_balance": float(c.credito_balance) if c.credito_balance else 0,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@bp.route("", methods=["GET"])
def listar():
    clientes = Cliente.query.order_by(Cliente.created_at.desc()).all()
    return jsonify([_cliente_json(c) for c in clientes])


@bp.route("", methods=["POST"])
def crear():
    data = request.get_json() or {}
    c = Cliente(
        nombre=data.get("nombre", ""),
        empresa=data.get("empresa"),
        industria=data.get("industria"),
        descripcion_negocio=data.get("descripcion_negocio"),
        tono_voz=data.get("tono_voz"),
        colores_preferidos=data.get("colores_preferidos"),
        referencias_visuales=data.get("referencias_visuales"),
        credito_balance=Decimal(str(data.get("credito_balance", 0))),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(_cliente_json(c)), 201


@bp.route("/<int:cid>", methods=["GET"])
def obtener(cid):
    c = Cliente.query.get_or_404(cid)
    return jsonify(_cliente_json(c))


@bp.route("/<int:cid>", methods=["PUT"])
def actualizar(cid):
    c = Cliente.query.get_or_404(cid)
    data = request.get_json() or {}
    for k in ["nombre", "empresa", "industria", "descripcion_negocio", "tono_voz", "colores_preferidos", "referencias_visuales"]:
        if k in data:
            setattr(c, k, data[k])
    if "credito_balance" in data:
        c.credito_balance = Decimal(str(data["credito_balance"]))
    db.session.commit()
    return jsonify(_cliente_json(c))


@bp.route("/<int:cid>", methods=["DELETE"])
def borrar(cid):
    c = Cliente.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return "", 204


@bp.route("/<int:cid>/prompts", methods=["GET"])
def listar_prompts(cid):
    prompts = Prompt.query.filter_by(cliente_id=cid).order_by(Prompt.created_at.desc()).limit(20).all()
    return jsonify([
        {
            "id": p.id,
            "tipo": p.tipo,
            "contenido": p.contenido,
            "correcciones": p.correcciones,
            "costo_usd": float(p.costo_usd) if p.costo_usd else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in prompts
    ])


@bp.route("/<int:cid>/prompts", methods=["POST"])
def crear_prompt(cid):
    Cliente.query.get_or_404(cid)
    data = request.get_json() or {}
    p = Prompt(
        cliente_id=cid,
        tipo=data.get("tipo", "imagen"),
        contenido=data.get("contenido", ""),
        correcciones=data.get("correcciones"),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id, "contenido": p.contenido}), 201


@bp.route("/<int:cid>/generar-prompt", methods=["POST"])
def generar_prompt(cid):
    c = Cliente.query.get_or_404(cid)
    data = request.get_json() or {}
    tipo = data.get("tipo", "imagen")
    contexto = data.get("contexto")
    modelo_override = data.get("modelo")
    ver_estructura = bool(data.get("ver_estructura"))
    messages = data.get("messages") or []
    solicitar_prompt_final = bool(data.get("solicitar_prompt_final"))
    try:
        result = svc_generar_prompt(
            c, tipo, contexto,
            modelo=modelo_override,
            messages=messages,
            solicitar_prompt_final=solicitar_prompt_final,
            ver_estructura=ver_estructura,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[Melo] generar-prompt error: {e}", flush=True)
        return jsonify({"error": f"Error OpenRouter: {str(e)}"}), 503
    contenido, costo, modelo = result[0], result[1], result[2]
    estructura = result[3] if len(result) > 3 else None
    out = {
        "contenido": contenido,
        "costo_usd": float(costo) if costo else None,
        "modelo": modelo,
        "es_prompt_final": solicitar_prompt_final,
    }
    if estructura:
        out["estructura"] = estructura
    # Solo guardar en BD cuando es el prompt final (no preguntas/respuestas)
    if solicitar_prompt_final:
        p = Prompt(cliente_id=cid, tipo=tipo, contenido=contenido, costo_usd=costo)
        db.session.add(p)
        db.session.commit()
        out["id"] = p.id
    return jsonify(out)


@bp.route("/<int:cid>/feedback", methods=["GET"])
def listar_feedback(cid):
    fbs = Feedback.query.filter_by(cliente_id=cid).order_by(Feedback.created_at.desc()).all()
    return jsonify([
        {"id": f.id, "contenido": f.contenido, "aplicado": f.aplicado, "created_at": f.created_at.isoformat() if f.created_at else None}
        for f in fbs
    ])


@bp.route("/<int:cid>/feedback", methods=["POST"])
def crear_feedback(cid):
    Cliente.query.get_or_404(cid)
    data = request.get_json() or {}
    f = Feedback(cliente_id=cid, contenido=data.get("contenido", ""))
    db.session.add(f)
    db.session.commit()
    return jsonify({"id": f.id, "contenido": f.contenido}), 201


@bp.route("/<int:cid>/feedback/<int:fid>/aplicar", methods=["PUT"])
def aplicar_feedback(cid, fid):
    c = Cliente.query.get_or_404(cid)
    f = Feedback.query.filter_by(id=fid, cliente_id=cid).first_or_404()
    if f.aplicado:
        return jsonify({"message": "Feedback ya aplicado"}), 400

    perfil = {
        "tono_voz": c.tono_voz,
        "colores_preferidos": c.colores_preferidos,
        "referencias_visuales": c.referencias_visuales,
    }
    updates = extraer_insights_de_feedback(f.contenido, perfil)
    for k, v in updates.items():
        if hasattr(c, k):
            setattr(c, k, v)
    f.aplicado = True
    db.session.commit()
    return jsonify(_cliente_json(c))


@bp.route("/<int:cid>/recargar-credito", methods=["POST"])
def recargar_credito(cid):
    c = Cliente.query.get_or_404(cid)
    data = request.get_json() or {}
    monto = Decimal(str(data.get("monto", 0)))
    nota = data.get("nota")
    if monto <= 0:
        return jsonify({"error": "El monto debe ser positivo"}), 400

    c.credito_balance = (c.credito_balance or Decimal("0")) + monto
    mov = CreditoMovimiento(cliente_id=cid, tipo="recarga", monto=monto, nota=nota)
    db.session.add(mov)
    db.session.commit()
    return jsonify(_cliente_json(c))


@bp.route("/<int:cid>/generar-media", methods=["POST"])
def generar_media(cid):
    c = Cliente.query.get_or_404(cid)
    data = request.get_json() or {}
    tipo = data.get("tipo", "imagen")
    prompt_texto = data.get("prompt", "").strip()
    instancia_id = data.get("instancia_id")

    if not prompt_texto:
        return jsonify({"error": "Se requiere el prompt"}), 400

    try:
        if instancia_id:
            inst = Instancia.query.filter_by(id=instancia_id, cliente_id=cid).first_or_404()
        else:
            inst = Instancia(cliente_id=cid, tipo=tipo)
            db.session.add(inst)
            db.session.flush()

        modelo_img = data.get("modelo")
        modelo_t2v = data.get("modelo_t2v")
        modelo_i2v = data.get("modelo_i2v")
        image_urls = data.get("image_urls") or []
        if isinstance(image_urls, str):
            image_urls = [image_urls] if image_urls.strip() else []
        image_url = data.get("image_url") or (image_urls[0] if image_urls else None)
        tail_image_url = data.get("tail_image_url") or (image_urls[1] if len(image_urls) > 1 else None)
        duration = data.get("duration", 5)
        if tipo == "imagen":
            url, costo, model = generar_imagen(prompt_texto, modelo=modelo_img, image_urls=image_urls if image_urls else None)
        elif tipo == "video":
            # Video: submit async para evitar timeout de Render (60-120s)
            req_id, model = submit_video(
                prompt_texto,
                image_url=image_url,
                tail_image_url=tail_image_url,
                duration=duration,
                modelo_t2v=modelo_t2v,
                modelo_i2v=modelo_i2v,
            )
            g = Generacion(
                cliente_id=cid, instancia_id=inst.id, tipo=tipo, costo_usd=Decimal("0"),
                estado="procesando", fal_request_id=req_id, fal_model=model
            )
            db.session.add(g)
            db.session.commit()
            return jsonify({
                "status": "procesando",
                "generacion_id": g.id,
                "instancia_id": inst.id,
                "url": None,
                "costo_usd": None,
                "modelo": model,
            }), 202
        elif tipo == "carrusel":
            num = int(data.get("num_imagenes", 3))
            urls = []
            costos = []
            model = None
            for _ in range(num):
                u, c, m = generar_imagen(prompt_texto, modelo=modelo_img)
                urls.append(u)
                costos.append(c)
                model = m
            costo_total = sum(costos)
            for u, c in zip(urls, costos):
                g = Generacion(cliente_id=cid, instancia_id=inst.id, tipo="carrusel", costo_usd=c, estado="pendiente", url_asset=u)
                db.session.add(g)
            db.session.commit()
            return jsonify({
                "url": urls[0] if urls else "",
                "generacion_id": g.id,
                "instancia_id": inst.id,
                "costo_usd": float(costo_total),
                "modelo": model,
            })
        else:
            return jsonify({"error": "tipo debe ser imagen, video o carrusel"}), 400

        g = Generacion(cliente_id=cid, instancia_id=inst.id, tipo=tipo, costo_usd=costo, estado="pendiente", url_asset=url)
        db.session.add(g)
        db.session.commit()
        return jsonify({
            "url": url,
            "generacion_id": g.id,
            "instancia_id": inst.id,
            "costo_usd": float(costo),
            "modelo": model,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback
        print(f"[Melo] generar-media error: {e}", flush=True)
        traceback.print_exc()
        err_msg = str(e)
        if "motivo_rechazo" in err_msg or "column" in err_msg.lower():
            err_msg = "Ejecuta: python migrate_motivo_rechazo.py"
        return jsonify({"error": f"Error: {err_msg}"}), 503


@bp.route("/<int:cid>/generaciones/<int:gid>/result", methods=["GET"])
def obtener_resultado_generacion(cid, gid):
    """Poll para video: obtiene el resultado cuando fal.ai termina."""
    c = Cliente.query.get_or_404(cid)
    g = Generacion.query.filter_by(id=gid, cliente_id=cid).first_or_404()
    if g.estado != "procesando" or not g.fal_request_id or not g.fal_model:
        return jsonify({
            "status": g.estado,
            "url": g.url_asset,
            "generacion_id": g.id,
            "costo_usd": float(g.costo_usd) if g.costo_usd else 0,
            "modelo": g.fal_model,
        })
    result = obtener_resultado_video(g.fal_request_id, g.fal_model)
    if result is None:
        return jsonify({"status": "procesando", "generacion_id": g.id}), 202
    url, costo, model = result
    g.url_asset = url
    g.costo_usd = costo
    g.estado = "pendiente"
    g.fal_request_id = None
    db.session.commit()
    return jsonify({
        "status": "pendiente",
        "url": url,
        "generacion_id": g.id,
        "instancia_id": g.instancia_id,
        "costo_usd": float(costo) if costo else 0,
        "modelo": model,
    })


@bp.route("/<int:cid>/generaciones", methods=["GET"])
def listar_generaciones(cid):
    gens = Generacion.query.filter_by(cliente_id=cid).order_by(Generacion.created_at.desc()).limit(50).all()
    return jsonify([
        {
            "id": g.id,
            "instancia_id": g.instancia_id,
            "tipo": g.tipo,
            "costo_usd": float(g.costo_usd) if g.costo_usd else 0,
            "estado": g.estado,
            "motivo_rechazo": getattr(g, "motivo_rechazo", None),
            "fal_request_id": getattr(g, "fal_request_id", None),
            "url_asset": g.url_asset,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in gens
    ])


@bp.route("/<int:cid>/generaciones/<int:gid>/aprobar", methods=["POST"])
def aprobar_generacion(cid, gid):
    c = Cliente.query.get_or_404(cid)
    g = Generacion.query.filter_by(id=gid, cliente_id=cid).first_or_404()
    if g.estado == "aprobada":
        return jsonify({"error": "Generación ya aprobada"}), 400

    inst = Instancia.query.get_or_404(g.instancia_id)
    if inst.cliente_id != cid:
        return jsonify({"error": "Instancia no pertenece al cliente"}), 400

    # Obtener tarifa desde DB
    tarifa = PrecioTarifa.query.filter_by(tipo=inst.tipo).first()
    if not tarifa:
        return jsonify({"error": f"No hay tarifa configurada para tipo {inst.tipo}"}), 400
    monto_cobrado = tarifa.precio

    if (c.credito_balance or Decimal("0")) < monto_cobrado:
        return jsonify({"error": "Crédito insuficiente"}), 400

    # Calcular costo total de todas las generaciones de la instancia
    todas = Generacion.query.filter_by(instancia_id=inst.id).all()
    costo_total = sum(x.costo_usd or Decimal("0") for x in todas)
    utilidad = monto_cobrado - costo_total

    # Marcar aprobada esta, rechazadas las demás
    for x in todas:
        x.estado = "aprobada" if x.id == gid else "rechazada"
    inst.monto_cobrado = monto_cobrado

    c.credito_balance = (c.credito_balance or Decimal("0")) - monto_cobrado
    mov = CreditoMovimiento(cliente_id=cid, tipo="consumo", monto=-monto_cobrado, referencia=inst.id, nota=f"Aprobación {inst.tipo}")
    db.session.add(mov)
    from app.models import RegistroContabilidad
    reg = RegistroContabilidad(cliente_id=cid, instancia_id=inst.id, monto_cobrado=monto_cobrado, costo_total_generaciones=costo_total, utilidad=utilidad)
    db.session.add(reg)
    db.session.commit()
    return jsonify({"message": "Aprobado", "cliente": _cliente_json(c)})


@bp.route("/<int:cid>/generaciones/<int:gid>/rechazar", methods=["POST"])
def rechazar_generacion(cid, gid):
    c = Cliente.query.get_or_404(cid)
    g = Generacion.query.filter_by(id=gid, cliente_id=cid).first_or_404()
    if g.estado != "pendiente":
        return jsonify({"error": "Solo se pueden rechazar generaciones pendientes"}), 400
    data = request.get_json() or {}
    motivo = (data.get("motivo") or "").strip()
    g.estado = "rechazada"
    g.motivo_rechazo = motivo or None
    db.session.commit()
    return jsonify({"message": "Rechazada", "cliente": _cliente_json(c)})


@bp.route("/<int:cid>/instancias", methods=["GET"])
def listar_instancias(cid):
    insts = Instancia.query.filter_by(cliente_id=cid).order_by(Instancia.created_at.desc()).limit(30).all()
    out = []
    for i in insts:
        gens = Generacion.query.filter_by(instancia_id=i.id).all()
        out.append({
            "id": i.id,
            "tipo": i.tipo,
            "monto_cobrado": float(i.monto_cobrado) if i.monto_cobrado else None,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "generaciones": [
                {"id": g.id, "estado": g.estado, "url_asset": g.url_asset, "costo_usd": float(g.costo_usd) if g.costo_usd else 0}
                for g in gens
            ],
        })
    return jsonify(out)
