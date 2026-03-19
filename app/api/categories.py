from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.client_info import ValueProposition, CompanyInfo, PreviousResults

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/value-propositions", methods=["GET"])
def list_value_propositions():
    items = ValueProposition.query.order_by(ValueProposition.name).all()
    return jsonify([_vp_to_dict(v) for v in items])


@categories_bp.route("/value-propositions", methods=["POST"])
def create_value_proposition():
    data = request.get_json()
    v = ValueProposition(name=data.get("name"), content=data.get("content"))
    db.session.add(v)
    db.session.commit()
    return jsonify(_vp_to_dict(v)), 201


@categories_bp.route("/value-propositions/<int:vid>", methods=["PUT", "PATCH"])
def update_value_proposition(vid):
    v = ValueProposition.query.get_or_404(vid)
    data = request.get_json()
    for key in ("name", "content"):
        if key in data:
            setattr(v, key, data[key])
    db.session.commit()
    return jsonify(_vp_to_dict(v))


@categories_bp.route("/value-propositions/<int:vid>", methods=["DELETE"])
def delete_value_proposition(vid):
    v = ValueProposition.query.get_or_404(vid)
    db.session.delete(v)
    db.session.commit()
    return "", 204


@categories_bp.route("/company-infos", methods=["GET"])
def list_company_infos():
    items = CompanyInfo.query.order_by(CompanyInfo.name).all()
    return jsonify([_ci_to_dict(c) for c in items])


@categories_bp.route("/company-infos", methods=["POST"])
def create_company_info():
    data = request.get_json()
    c = CompanyInfo(name=data.get("name"), content=data.get("content"))
    db.session.add(c)
    db.session.commit()
    return jsonify(_ci_to_dict(c)), 201


@categories_bp.route("/company-infos/<int:cid>", methods=["PUT", "PATCH"])
def update_company_info(cid):
    c = CompanyInfo.query.get_or_404(cid)
    data = request.get_json()
    for key in ("name", "content"):
        if key in data:
            setattr(c, key, data[key])
    db.session.commit()
    return jsonify(_ci_to_dict(c))


@categories_bp.route("/company-infos/<int:cid>", methods=["DELETE"])
def delete_company_info(cid):
    c = CompanyInfo.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return "", 204


@categories_bp.route("/previous-results", methods=["GET"])
def list_previous_results():
    items = PreviousResults.query.order_by(PreviousResults.name).all()
    return jsonify([_pr_to_dict(p) for p in items])


@categories_bp.route("/previous-results", methods=["POST"])
def create_previous_results():
    data = request.get_json()
    p = PreviousResults(name=data.get("name"), content=data.get("content"))
    db.session.add(p)
    db.session.commit()
    return jsonify(_pr_to_dict(p)), 201


@categories_bp.route("/previous-results/<int:pid>", methods=["PUT", "PATCH"])
def update_previous_results(pid):
    p = PreviousResults.query.get_or_404(pid)
    data = request.get_json()
    for key in ("name", "content"):
        if key in data:
            setattr(p, key, data[key])
    db.session.commit()
    return jsonify(_pr_to_dict(p))


@categories_bp.route("/previous-results/<int:pid>", methods=["DELETE"])
def delete_previous_results(pid):
    p = PreviousResults.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return "", 204


def _vp_to_dict(v):
    return {"id": v.id, "name": v.name, "content": v.content}


def _ci_to_dict(c):
    return {"id": c.id, "name": c.name, "content": c.content}


def _pr_to_dict(p):
    return {"id": p.id, "name": p.name, "content": p.content}
