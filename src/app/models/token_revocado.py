import datetime

from app.core.database import get_db


class TokenRevocado:
    @staticmethod
    def esta_revocado(jti: str) -> bool:
        cur = get_db().cursor()
        cur.execute("SELECT 1 FROM tokens_revocados WHERE jti = %s", (jti,))
        fila = cur.fetchone()
        cur.close()
        return fila is not None

    @staticmethod
    def revocar(jti: str, expira_en: datetime.datetime) -> None:
        cur = get_db().cursor()
        cur.execute(
            "INSERT IGNORE INTO tokens_revocados (jti, expira_en) VALUES (%s, %s)",
            (jti, expira_en.strftime("%Y-%m-%d %H:%M:%S")),
        )
        cur.close()
