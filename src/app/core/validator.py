import json
from functools import lru_cache
from pathlib import Path

import jsonschema_rs

from app.core.errors import ApiException

# valida el body de una request contra un JSON Schema (app/schemas/*.json) y
# traduce los errores al mismo formato { campo: mensaje } que ya espera
# ApiException.validacion() -- el contrato JSON de un 422 no cambia, solo
# como se arma internamente. El trim/normalizacion de strings sigue siendo
# responsabilidad de cada ruta, antes de llamar a validar().
_DIR_SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"


@lru_cache(maxsize=None)
def _validador(nombre_schema: str):
    ruta = _DIR_SCHEMAS / f"{nombre_schema}.json"
    schema = json.loads(ruta.read_text())
    return jsonschema_rs.validator_for(schema)


def validar(nombre_schema: str, datos: dict) -> None:
    errores: dict[str, str] = {}

    for error in _validador(nombre_schema).iter_errors(datos):
        campo, mensaje = _traducir(error)
        errores.setdefault(campo, mensaje)

    if errores:
        raise ApiException.validacion(errores)


def _traducir(error) -> tuple[str, str]:
    kind = error.kind
    args = kind.as_dict()

    # 'required' no tiene instance_path util (apunta al objeto entero, no al
    # campo que falta): el nombre del campo viene en kind.as_dict()['property'].
    if kind.name == "required":
        return args["property"], "Requerido."

    campo = "/".join(str(p) for p in error.instance_path) or "?"

    if kind.name == "minLength":
        # minLength:1 se usa para "no vacio"; cualquier otro limite es un
        # minimo de longitud real y necesita su propio mensaje.
        return campo, "Requerido." if args["limit"] <= 1 else f"Minimo {args['limit']} caracteres."
    if kind.name == "maxLength":
        return campo, f"Maximo {args['limit']} caracteres."
    if kind.name == "type":
        return campo, _mensaje_tipo(args.get("types"))
    return campo, "Dato invalido."


def _mensaje_tipo(tipos) -> str:
    tipo = tipos[0] if tipos else None
    return {
        "string": "Tiene que ser texto.",
        "integer": "Tiene que ser un numero entero.",
        "number": "Tiene que ser numerico.",
    }.get(tipo, "Tipo de dato invalido.")
