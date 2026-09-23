import datetime

from flask import Blueprint, jsonify

from app.core.database import get_db

bp = Blueprint("ping", __name__)


# GET /api/ping
@bp.get("/ping")
def ping():
    return jsonify({"pong": True, "hora": datetime.datetime.now(datetime.timezone.utc).isoformat()})


# GET /api/health/db
@bp.get("/health/db")
def health_db():
    cur = get_db().cursor()
    cur.execute("SELECT 1")
    cur.fetchone()
    cur.close()
    return jsonify({"db": "ok"})
