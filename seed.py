"""Script para poblar la base de datos inicial."""
import os
import sys

# Asegurar que estamos en el directorio correcto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Cliente, PrecioTarifa, ModeloDefault
from decimal import Decimal


def seed():
    app = create_app()
    with app.app_context():
        # Modelos por defecto (OpenRouter para prompt, fal.ai para imagen/video)
        modelos_default = [
            ("prompt", "openai/gpt-4o-mini"),
            ("imagen", "fal-ai/flux/dev"),
            ("imagen_editar", "fal-ai/flux-2/turbo/edit"),
            ("video_t2v", "fal-ai/ltx-video-13b-distilled"),
            ("video_i2v", "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"),
        ]
        for clave, modelo in modelos_default:
            md = ModeloDefault.query.filter_by(clave=clave).first()
            if not md:
                md = ModeloDefault(clave=clave, modelo=modelo)
                db.session.add(md)
                print(f"  Creado ModeloDefault: {clave} = {modelo}")

        # Precios por defecto
        for tipo, precio in [("imagen", 10), ("carrusel", 30), ("video", 50)]:
            pt = PrecioTarifa.query.filter_by(tipo=tipo).first()
            if not pt:
                pt = PrecioTarifa(tipo=tipo, precio=Decimal(str(precio)))
                db.session.add(pt)
                print(f"  Creado PrecioTarifa: {tipo} = {precio}")

        # Clientes de prueba
        if Cliente.query.count() == 0:
            c1 = Cliente(
                nombre="Tienda Demo",
                empresa="Demo SRL",
                industria="Retail",
                descripcion_negocio="Tienda de ropa vintage online",
                tono_voz="Casual y amigable",
                colores_preferidos="#8B4513, #F5DEB3",
                credito_balance=Decimal("100"),
            )
            c2 = Cliente(
                nombre="Café Central",
                empresa="Café Central",
                industria="Gastronomía",
                descripcion_negocio="Cafetería de especialidad en centro",
                tono_voz="Acogedor, premium",
                colores_preferidos="#4A3728, #D4A574",
                credito_balance=Decimal("50"),
            )
            db.session.add_all([c1, c2])
            print("  Creados 2 clientes de prueba")

        db.session.commit()
        print("Seed completado.")


if __name__ == "__main__":
    seed()
