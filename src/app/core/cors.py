from flask import current_app, request, Response


# CORS manual, sin flask-cors: el starter no suma una dependencia solo para
# esto, misma filosofia que los hermanos PHP (que setean los headers a mano en
# public/index.php). Se aplica a TODA respuesta y el preflight OPTIONS se
# contesta ahi mismo con 204, antes de llegar a cualquier blueprint.
def register_cors(app):
    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return Response(status=204)

    @app.after_request
    def _add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = current_app.config["CORS_ORIGIN"]
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Vary"] = "Origin"
        return response
