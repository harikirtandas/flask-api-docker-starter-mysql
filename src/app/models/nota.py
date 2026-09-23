from app.core.database import get_db

# modelo de ejemplo del vertical slice demo, descartable. Un CRUD minimo
# (notas de un usuario) que sirve para probar de punta a punta el router de
# Flask, el pool/conexion de mysql-connector-python, y la auth JWT juntos. En
# un proyecto real se borra entero y se reemplaza por los modelos del dominio
# (misma logica que App\Models\Nota en los hermanos PHP).


class Nota:
    @staticmethod
    def del_usuario(usuario_id: int) -> list[dict]:
        cur = get_db().cursor(dictionary=True)
        cur.execute(
            "SELECT id, titulo, cuerpo, created_at, updated_at "
            "FROM notas WHERE usuario_id = %s ORDER BY id DESC",
            (usuario_id,),
        )
        filas = cur.fetchall()
        cur.close()
        return filas

    @staticmethod
    def buscar_de_usuario(id_: int, usuario_id: int) -> dict | None:
        cur = get_db().cursor(dictionary=True)
        cur.execute(
            "SELECT id, titulo, cuerpo, created_at, updated_at "
            "FROM notas WHERE id = %s AND usuario_id = %s",
            (id_, usuario_id),
        )
        fila = cur.fetchone()
        cur.close()
        return fila

    @staticmethod
    def crear(usuario_id: int, titulo: str, cuerpo: str) -> int:
        cur = get_db().cursor()
        cur.execute(
            "INSERT INTO notas (usuario_id, titulo, cuerpo, created_at, updated_at) "
            "VALUES (%s, %s, %s, NOW(), NOW())",
            (usuario_id, titulo, cuerpo),
        )
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id

    @staticmethod
    def actualizar(id_: int, usuario_id: int, titulo: str, cuerpo: str) -> bool:
        cur = get_db().cursor()
        cur.execute(
            "UPDATE notas SET titulo = %s, cuerpo = %s, updated_at = NOW() "
            "WHERE id = %s AND usuario_id = %s",
            (titulo, cuerpo, id_, usuario_id),
        )
        afectadas = cur.rowcount
        cur.close()
        return afectadas > 0

    @staticmethod
    def eliminar(id_: int, usuario_id: int) -> bool:
        cur = get_db().cursor()
        cur.execute(
            "DELETE FROM notas WHERE id = %s AND usuario_id = %s",
            (id_, usuario_id),
        )
        afectadas = cur.rowcount
        cur.close()
        return afectadas > 0
