from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.auth import generar_token, revocar_token_actual, usuario_actual
from app.core.errors import ApiException
from app.models.usuario import Usuario

bp = Blueprint("auth", __name__)


# POST /api/auth/register   { "nombre": "...", "email": "...", "password": "..." }
# No existe en los hermanos PHP (ahi el usuario demo se precarga por SQL); se
# suma aca porque un login por JWT sin alta propia es poco realista para un
# proyecto que arranca de este starter.
@bp.post("/register")
def register():
    nombre = (request.get_json(silent=True) or {}).get("nombre", "").strip()
    email = (request.get_json(silent=True) or {}).get("email", "").strip().lower()
    password = (request.get_json(silent=True) or {}).get("password", "")

    errores = {}
    if not nombre:
        errores["nombre"] = "Requerido."
    if not email:
        errores["email"] = "Requerido."
    if len(password) < 6:
        errores["password"] = "Minimo 6 caracteres."
    if errores:
        raise ApiException.validacion(errores)

    if Usuario.por_email(email) is not None:
        raise ApiException.validacion({"email": "Ya existe un usuario con ese email."})

    password_hash = generate_password_hash(password, method="pbkdf2:sha256")
    nuevo_id = Usuario.crear(nombre, email, password_hash)
    usuario = Usuario.buscar_por_id(nuevo_id)
    usuario.pop("password_hash", None)

    return jsonify(usuario), 201


# POST /api/auth/login   { "email": "...", "password": "..." }
@bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    usuario = Usuario.por_email(email)

    # mismo mensaje para "no existe" y "password mala": no filtra si el email
    # esta registrado.
    if usuario is None or not check_password_hash(usuario["password_hash"], password):
        raise ApiException(401, "Email o contrasena incorrectos.")

    token, expira = generar_token(usuario)
    usuario.pop("password_hash", None)

    return jsonify({"token": token, "expira": expira, "usuario": usuario})


# GET /api/auth/me
@bp.get("/me")
def me():
    return jsonify(usuario_actual())


# POST /api/auth/logout
@bp.post("/logout")
def logout():
    revocar_token_actual()
    return "", 204
