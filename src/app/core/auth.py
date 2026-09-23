import datetime
import uuid

import jwt
from flask import current_app, request

from app.core.errors import ApiException
from app.models.token_revocado import TokenRevocado
from app.models.usuario import Usuario

# Autenticacion por JWT (a diferencia de los hermanos PHP, que usan un token
# opaco en tabla). El JWT en si es sin estado -- la firma alcanza para
# validarlo sin ir a la base -- salvo por logout: revocar un token ANTES de su
# "exp" natural requiere guardar su "jti" en algun lado hasta que venza solo.
# Esa lista negra minima vive en TokenRevocado.
#
# Flujo:
#   POST /api/auth/login    -> generar_token()  -> { token, expira, usuario }
#   requests siguientes     -> header Authorization: Bearer <token>
#   en cada request protegida -> usuario_actual(), llamado explicito al
#     principio del metodo del blueprint (no hay decorator/middleware: mismo
#     criterio que Auth::usuarioActual($request) en los hermanos PHP, para que
#     quede a la vista que endpoint pide sesion con solo leer su primera linea)


def generar_token(usuario: dict) -> tuple[str, str]:
    """Emite un JWT para el usuario dado.

    @return (token, expira_en) con expira_en como "YYYY-MM-DD HH:MM:SS" (UTC)
    """
    ttl_horas = current_app.config["JWT_TTL_HORAS"]
    ahora = datetime.datetime.now(datetime.timezone.utc)
    expira = ahora + datetime.timedelta(hours=ttl_horas)

    payload = {
        # "sub" tiene que ser string: PyJWT valida que cumpla StringOrURI
        # (RFC 7519) y rechaza un int con InvalidSubjectError.
        "sub": str(usuario["id"]),
        "jti": str(uuid.uuid4()),
        "iat": ahora,
        "exp": expira,
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")

    return token, expira.strftime("%Y-%m-%d %H:%M:%S")


def _bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def _decodificar(token: str, *, verificar_exp: bool = True) -> dict:
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"],
            options={"verify_exp": verificar_exp},
        )
    except jwt.ExpiredSignatureError:
        raise ApiException(401, "Token vencido.")
    except jwt.InvalidTokenError:
        raise ApiException(401, "Token invalido.")


def usuario_actual() -> dict:
    """Resuelve el Bearer token de la request al usuario dueno, o corta con 401.

    @return fila de `usuarios` sin password_hash
    """
    token = _bearer_token()
    if token is None:
        raise ApiException(401, "Falta el header Authorization: Bearer <token>.")

    payload = _decodificar(token)

    if TokenRevocado.esta_revocado(payload["jti"]):
        raise ApiException(401, "Token invalido o vencido.")

    usuario = Usuario.buscar_por_id(int(payload["sub"]))
    if usuario is None:
        raise ApiException(401, "Token invalido o vencido.")

    usuario.pop("password_hash", None)
    return usuario


def revocar_token_actual() -> None:
    """Invalida el token actual (lo agrega a la lista negra). No falla si el
    header no vino o el token ya es invalido: logout siempre "funciona" desde
    el punto de vista del cliente."""
    token = _bearer_token()
    if token is None:
        return

    try:
        payload = _decodificar(token, verificar_exp=False)
    except ApiException:
        return

    expira_en = datetime.datetime.fromtimestamp(payload["exp"], tz=datetime.timezone.utc)
    TokenRevocado.revocar(payload["jti"], expira_en)
