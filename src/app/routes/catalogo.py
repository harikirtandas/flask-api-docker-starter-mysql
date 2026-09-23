from flask import Blueprint, jsonify, request

from app.core.external_catalog import ExternalCatalogClient

bp = Blueprint("catalogo", __name__)

# Demo generico de "como consumir un catalogo externo de solo lectura" (ver
# app/core/external_catalog.py). No es el dominio del proyecto final -- es un
# proxy de juguete parametrizado por <recurso> para poder probarlo sin
# configurar nada especifico. Para el proyecto real (API del Profesor) se
# reemplaza por dos blueprints concretos, "lenguajes" y "tecnologias", cada uno
# con SOLO el verbo GET (nunca POST/PUT/DELETE: son catalogos ajenos de solo
# lectura) y usando el mismo ExternalCatalogClient tal cual, por ejemplo:
#
#   @bp.get("")
#   def index():
#       return jsonify(cliente.listar("tecnologias", params={"nombre": request.args.get("nombre")}))
#
#   @bp.get("/<int:id_>")
#   def show(id_):
#       return jsonify(cliente.obtener("tecnologias", id_))
#
# apuntando EXTERNAL_API_BASE_URL a la URL base real y EXTERNAL_API_KEY a la
# clave que le entreguen al grupo (nunca hardcodeada, nunca en el cliente JS).

cliente = ExternalCatalogClient()


# GET /api/catalogo/<recurso>?<query>
@bp.get("/<recurso>")
def index(recurso: str):
    return jsonify(cliente.listar(recurso, params=request.args.to_dict()))


# GET /api/catalogo/<recurso>/<id>
@bp.get("/<recurso>/<id_>")
def show(recurso: str, id_: str):
    return jsonify(cliente.obtener(recurso, id_))
