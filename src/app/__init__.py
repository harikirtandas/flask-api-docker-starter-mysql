from flask import Flask

from config import Config

from app.core.database import close_db
from app.core.errors import register_error_handlers
from app.core.cors import register_cors


def create_app():
    # static_folder=None: esta app es solo API, no sirve nada de HTML/JS/CSS
    # (eso vive en ../web/, otro proceso/puerto). Sin esto, Flask registra
    # igual una ruta /static/<path:filename> por default, apuntando a una
    # carpeta que ya no existe.
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    register_cors(app)
    register_error_handlers(app)
    app.teardown_appcontext(close_db)

    from app.routes import ping, auth, notas, catalogo

    ping.registrar_rutas(app)
    auth.registrar_rutas(app)
    notas.registrar_rutas(app)
    catalogo.registrar_rutas(app)

    return app
