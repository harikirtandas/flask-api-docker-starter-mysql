from app import create_app

# punto de entrada para "flask run" (ver CMD en docker/Dockerfile) y para
# cualquier servidor WSGI real en produccion (gunicorn wsgi:app, etc.).
app = create_app()
