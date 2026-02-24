"""Migración: añade columna motivo_rechazo a generaciones si no existe."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text, inspect

def migrate():
    app = create_app()
    with app.app_context():
        insp = inspect(db.engine)
        cols = [c["name"] for c in insp.get_columns("generaciones")]
        if "motivo_rechazo" in cols:
            print("Columna motivo_rechazo ya existe.")
            return
        db.session.execute(text("ALTER TABLE generaciones ADD COLUMN motivo_rechazo TEXT"))
        db.session.commit()
        print("Columna motivo_rechazo añadida.")

if __name__ == "__main__":
    migrate()
