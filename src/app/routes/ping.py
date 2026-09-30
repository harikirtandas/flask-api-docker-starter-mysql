import datetime

from flask import jsonify

from app.core.database import get_db


def registrar_rutas(app):
    # GET /api/ping
    @app.get("/api/ping")
    def ping():
        return jsonify({"pong": True, "hora": datetime.datetime.now(datetime.timezone.utc).isoformat()})

    # GET /api/health/db
    @app.get("/api/health/db")
    def health_db():
        cur = get_db().cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        return jsonify({"db": "ok"})
