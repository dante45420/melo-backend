"""Modelos de base de datos."""
from datetime import datetime
from decimal import Decimal
from app import db


class Cliente(db.Model):
    """Cliente del servicio de marketing."""
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    empresa = db.Column(db.String(200))
    industria = db.Column(db.String(200))
    descripcion_negocio = db.Column(db.Text)
    tono_voz = db.Column(db.String(200))
    colores_preferidos = db.Column(db.String(500))
    referencias_visuales = db.Column(db.JSON)
    credito_balance = db.Column(db.Numeric(12, 2), default=Decimal('0'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prompts = db.relationship('Prompt', backref='cliente', lazy='dynamic', foreign_keys='Prompt.cliente_id')
    feedbacks = db.relationship('Feedback', backref='cliente', lazy='dynamic')
    instancias = db.relationship('Instancia', backref='cliente', lazy='dynamic')
    generaciones = db.relationship('Generacion', backref='cliente', lazy='dynamic', foreign_keys='Generacion.cliente_id')
    creditos = db.relationship('CreditoMovimiento', backref='cliente', lazy='dynamic')


class Prompt(db.Model):
    """Prompt generado por OpenRouter."""
    __tablename__ = 'prompts'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # imagen, video
    contenido = db.Column(db.Text, nullable=False)
    correcciones = db.Column(db.JSON)
    costo_usd = db.Column(db.Numeric(10, 6), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    """Feedback del cliente sobre generaciones."""
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    aplicado = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Instancia(db.Model):
    """Agrupa generaciones de un mismo trabajo (imagen, carrusel, video)."""
    __tablename__ = 'instancias'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # imagen, carrusel, video
    monto_cobrado = db.Column(db.Numeric(12, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    generaciones = db.relationship('Generacion', backref='instancia', lazy='dynamic')


class Generacion(db.Model):
    """Una generación de imagen o video (fal.ai)."""
    __tablename__ = 'generaciones'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    instancia_id = db.Column(db.Integer, db.ForeignKey('instancias.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # imagen, carrusel, video
    costo_usd = db.Column(db.Numeric(10, 6), default=Decimal('0'))
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, aprobada, rechazada
    url_asset = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CreditoMovimiento(db.Model):
    """Movimiento de créditos (recarga o consumo)."""
    __tablename__ = 'credito_movimientos'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # recarga, consumo
    monto = db.Column(db.Numeric(12, 2), nullable=False)  # positivo=recarga, negativo=consumo
    referencia = db.Column(db.Integer, nullable=True)  # instancia_id
    nota = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RegistroContabilidad(db.Model):
    """Registro de utilidad por cada aprobación."""
    __tablename__ = 'registro_contabilidad'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    instancia_id = db.Column(db.Integer, db.ForeignKey('instancias.id'), nullable=False)
    monto_cobrado = db.Column(db.Numeric(12, 2), nullable=False)
    costo_total_generaciones = db.Column(db.Numeric(12, 6), nullable=False)
    utilidad = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Cliente', backref='registros_contabilidad')
    instancia = db.relationship('Instancia', backref='registro_contabilidad')


class PrecioTarifa(db.Model):
    """Precio por tipo (imagen, carrusel, video) - editable desde la web."""
    __tablename__ = 'precio_tarifas'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), unique=True, nullable=False)
    precio = db.Column(db.Numeric(12, 2), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
