from flask import Blueprint, jsonify, request

from app.core.auth import usuario_actual
from app.core.errors import ApiException
from app.models.nota import Nota

bp = Blueprint("notas", __name__)

# slice demo: CRUD completo de "notas" de un usuario. Cada endpoint llama
# usuario_actual() como primera linea (guard explicito, sin decorator) y solo
# ve/toca las notas del usuario dueno del token. Descartable.


def _validar_cuerpo() -> tuple[str, str]:
    body = request.get_json(silent=True) or {}
    titulo = str(body.get("titulo", "")).strip()
    cuerpo = str(body.get("cuerpo", "")).strip()

    errores = {}
    if not titulo:
        errores["titulo"] = "Requerido."
    elif len(titulo) > 120:
        errores["titulo"] = "Maximo 120 caracteres."
    if errores:
        raise ApiException.validacion(errores)

    return titulo, cuerpo


# GET /api/notas
@bp.get("")
def index():
    usuario = usuario_actual()
    return jsonify({"datos": Nota.del_usuario(usuario["id"])})


# GET /api/notas/{id}
@bp.get("/<int:id_>")
def show(id_: int):
    usuario = usuario_actual()
    nota = Nota.buscar_de_usuario(id_, usuario["id"])
    if nota is None:
        raise ApiException(404, "Nota no encontrada.")
    return jsonify(nota)


# POST /api/notas   { "titulo": "...", "cuerpo": "..." }
@bp.post("")
def store():
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
@bp.route("/<int:id_>", methods=["PUT", "PATCH"])
def update(id_: int):
    usuario = usuario_actual()
    if Nota.buscar_de_usuario(id_, usuario["id"]) is None:
        raise ApiException(404, "Nota no encontrada.")

    titulo, cuerpo = _validar_cuerpo()
    Nota.actualizar(id_, usuario["id"], titulo, cuerpo)

    return jsonify(Nota.buscar_de_usuario(id_, usuario["id"]))


# DELETE /api/notas/{id}
@bp.delete("/<int:id_>")
def destroy(id_: int):
    usuario = usuario_actual()
    if not Nota.eliminar(id_, usuario["id"]):
        raise ApiException(404, "Nota no encontrada.")
    return "", 204
