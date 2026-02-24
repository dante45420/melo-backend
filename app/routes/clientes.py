"""Rutas de clientes."""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Cliente, Prompt, Feedback, Instancia, Generacion, CreditoMovimiento, PrecioTarifa
from decimal import Decimal
from app.services.prompt_generator import generar_prompt as svc_generar_prompt
from app.services.media_generator import generar_imagen, generar_video
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

    contenido, costo = svc_generar_prompt(c, tipo, contexto)
    p = Prompt(cliente_id=cid, tipo=tipo, contenido=contenido, costo_usd=costo)
    db.session.add(p)
    db.session.commit()
    return jsonify({
        "id": p.id,
        "contenido": contenido,
        "costo_usd": float(costo) if costo else None,
    })


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

    if instancia_id:
        inst = Instancia.query.filter_by(id=instancia_id, cliente_id=cid).first_or_404()
    else:
        inst = Instancia(cliente_id=cid, tipo=tipo)
        db.session.add(inst)
        db.session.flush()  # obtener id

    if tipo == "imagen":
        url, costo = generar_imagen(prompt_texto)
    elif tipo == "video":
        url, costo = generar_video(prompt_texto, data.get("image_url"))
    elif tipo == "carrusel":
        num = int(data.get("num_imagenes", 3))
        urls = []
        costos = []
        for _ in range(num):
            u, c = generar_imagen(prompt_texto)
            urls.append(u)
            costos.append(c)
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
