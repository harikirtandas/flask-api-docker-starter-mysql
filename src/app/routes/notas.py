from flask import jsonify, request

from app.core.auth import usuario_actual
from app.core.errors import ApiException
from app.core.validator import validar
from app.models.nota import Nota

# slice demo: CRUD completo de "notas" de un usuario. Cada endpoint llama
# usuario_actual() como primera linea (guard explicito, sin decorator) y solo
# ve/toca las notas del usuario dueno del token. Descartable.


def _validar_cuerpo() -> tuple[str, str]:
    body = request.get_json(silent=True) or {}
    datos = {
        "titulo": str(body.get("titulo", "")).strip(),
        "cuerpo": str(body.get("cuerpo", "")).strip(),
    }
    validar("notas", datos)
    return datos["titulo"], datos["cuerpo"]


def registrar_rutas(app):
    # Los nombres de las funciones vista tienen que ser unicos en toda la app
    # (Flask deriva el nombre de endpoint de func.__name__ cuando no se pasa
    # endpoint=; sin Blueprints, que namespacean por su cuenta, dos modulos
    # con una funcion "index"/"show" cada uno pisan el mismo endpoint y
    # create_app() explota con AssertionError al arrancar). Por eso index/show
    # llevan el prefijo notas_ -- catalogo.py define su propio index/show y
    # colisionaria sin esto.

    # GET /api/notas
    @app.get("/api/notas")
    def notas_index():
        usuario = usuario_actual()
        return jsonify({"datos": Nota.del_usuario(usuario["id"])})

    # GET /api/notas/{id}
    @app.get("/api/notas/<int:id_>")
    def notas_show(id_: int):
        usuario = usuario_actual()
        nota = Nota.buscar_de_usuario(id_, usuario["id"])
        if nota is None:
            raise ApiException(404, "Nota no encontrada.")
        return jsonify(nota)

    # POST /api/notas   { "titulo": "...", "cuerpo": "..." }
    @app.post("/api/notas")
    def notas_store():
        usuario = usuario_actual()
        titulo, cuerpo = _validar_cuerpo()

        nuevo_id = Nota.crear(usuario["id"], titulo, cuerpo)
        nota = Nota.buscar_de_usuario(nuevo_id, usuario["id"])

        response = jsonify(nota)
        response.status_code = 201
        response.headers["Location"] = f"/api/notas/{nuevo_id}"
        return response

    # PUT/PATCH /api/notas/{id}   { "titulo": "...", "cuerpo": "..." }
    # (igual que en los hermanos PHP: PATCH esta registrado contra el mismo
    # metodo que PUT, es un reemplazo completo, no un merge parcial de campos)
    @app.route("/api/notas/<int:id_>", methods=["PUT", "PATCH"])
    def notas_update(id_: int):
        usuario = usuario_actual()
        if Nota.buscar_de_usuario(id_, usuario["id"]) is None:
            raise ApiException(404, "Nota no encontrada.")

        titulo, cuerpo = _validar_cuerpo()
        Nota.actualizar(id_, usuario["id"], titulo, cuerpo)

        return jsonify(Nota.buscar_de_usuario(id_, usuario["id"]))

    # DELETE /api/notas/{id}
    @app.delete("/api/notas/<int:id_>")
    def notas_destroy(id_: int):
        usuario = usuario_actual()
        if not Nota.eliminar(id_, usuario["id"]):
            raise ApiException(404, "Nota no encontrada.")
        return "", 204
