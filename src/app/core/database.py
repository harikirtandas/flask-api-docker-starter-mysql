import mysql.connector
from flask import current_app, g

# una conexion por request, guardada en flask.g y cerrada en el
# teardown_appcontext registrado desde create_app(). Es el patron oficial de
# Flask para recursos con ciclo de vida atado al request (ver docs de
# "Application Context"). Equivalente en espiritu al singleton PDO de los
# hermanos PHP: alli un proceso mod_php vive un solo request y su PDO muere
# con el; aca el proceso Flask sigue vivo entre requests, asi que "g" es lo que
# acota la conexion a UN request en vez de compartirla entre todos.
def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            database=current_app.config["DB_DATABASE"],
            user=current_app.config["DB_USERNAME"],
            password=current_app.config["DB_PASSWORD"],
            charset="utf8mb4",
            autocommit=True,
        )
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()
