from app.core.database import get_db


class Usuario:
    @staticmethod
    def por_email(email: str) -> dict | None:
        cur = get_db().cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        fila = cur.fetchone()
        cur.close()
        return fila

    @staticmethod
    def buscar_por_id(id_: int) -> dict | None:
        cur = get_db().cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE id = %s", (id_,))
        fila = cur.fetchone()
        cur.close()
        return fila

    @staticmethod
    def crear(nombre: str, email: str, password_hash: str) -> int:
        cur = get_db().cursor()
        cur.execute(
            "INSERT INTO usuarios (nombre, email, password_hash) VALUES (%s, %s, %s)",
            (nombre, email, password_hash),
        )
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id
