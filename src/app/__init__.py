from flask import Flask

from config import Config

from app.core.database import close_db
from app.core.errors import register_error_handlers
from app.core.cors import register_cors


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(Config)

    register_cors(app)
    register_error_handlers(app)
    app.teardown_appcontext(close_db)

    # Flask solo mapea static_folder a partir de "/<path:filename>": una
    # request a "/" no matchea eso (filename quedaria vacio), asi que el
    # cliente demo necesita esta ruta explicita para servir su index.html.
    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    from app.routes.ping import bp as ping_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.notas import bp as notas_bp
    from app.routes.catalogo import bp as catalogo_bp

    app.register_blueprint(ping_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(notas_bp, url_prefix="/api/notas")
    app.register_blueprint(catalogo_bp, url_prefix="/api/catalogo")

    return app
