from flask import jsonify, request

from app.core.external_catalog import ExternalCatalogClient

# Demo generico de "como consumir un catalogo externo de solo lectura" (ver
# app/core/external_catalog.py). No es el dominio del proyecto final -- es un
# proxy de juguete parametrizado por <recurso> para poder probarlo sin
# configurar nada especifico. Para el proyecto real (API del Profesor) se
# reemplaza por dos rutas concretas, "lenguajes" y "tecnologias", cada una
# con SOLO el verbo GET (nunca POST/PUT/DELETE: son catalogos ajenos de solo
# lectura) y usando el mismo ExternalCatalogClient tal cual, por ejemplo:
#
#   @app.get("/api/tecnologias")
#   def tecnologias_index():
#       return jsonify(cliente.listar("tecnologias", params={"nombre": request.args.get("nombre")}))
#
#   @app.get("/api/tecnologias/<int:id_>")
#   def tecnologias_show(id_):
#       return jsonify(cliente.obtener("tecnologias", id_))
#
# apuntando EXTERNAL_API_BASE_URL a la URL base real y EXTERNAL_API_KEY a la
# clave que le entreguen al grupo (nunca hardcodeada, nunca en el cliente JS).

cliente = ExternalCatalogClient()


def registrar_rutas(app):
    # index/show llevan el prefijo catalogo_ para no colisionar con los
    # homonimos de notas.py -- ver comentario en notas.py.registrar_rutas().

    # GET /api/catalogo/<recurso>?<query>
    @app.get("/api/catalogo/<recurso>")
    def catalogo_index(recurso: str):
        return jsonify(cliente.listar(recurso, params=request.args.to_dict()))

    # GET /api/catalogo/<recurso>/<id>
    @app.get("/api/catalogo/<recurso>/<id_>")
    def catalogo_show(recurso: str, id_: str):
        return jsonify(cliente.obtener(recurso, id_))
