# Melo Backend

Flask API para panel admin. Desplegar en Render.

## Configuración

Copiar `.env.example` a `.env` y configurar:

```
ADMIN_USER=tu_usuario
ADMIN_PASSWORD=tu_contraseña
SECRET_KEY=clave-segura-para-sesiones
```

## Desarrollo

```bash
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
python run.py
```

Login: http://localhost:5000/login

## Git (repos separados)

```bash
git init
git remote add origin https://github.com/dante45420/melo-backend.git
```
