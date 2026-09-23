from flask import current_app, jsonify


class ApiException(Exception):
    """Excepcion de la capa HTTP: lleva el status que hay que devolver y,
    opcionalmente, un detalle de errores de validacion campo -> mensaje.
    register_error_handlers() la traduce a JSON. Mismo contrato de error que
    los hermanos PHP (App\\Core\\ApiException), a proposito: un cliente (o
    Bruno) que ya sabe leer { "error": { status, mensaje, errores } } de un
    starter de la familia lo sabe leer de todos.

        raise ApiException(404, "Nota no encontrada.")
        raise ApiException.validacion({"email": "Formato invalido"})
    """

    def __init__(self, status: int, mensaje: str, errores: dict | None = None):
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje
        self.errores = errores or {}

    @classmethod
    def validacion(cls, errores: dict, mensaje: str = "Datos invalidos.") -> "ApiException":
        return cls(422, mensaje, errores)


def register_error_handlers(app):
    @app.errorhandler(ApiException)
    def _handle_api_exception(e: ApiException):
        payload = {"status": e.status, "mensaje": e.mensaje}
        if e.errores:
            payload["errores"] = e.errores
        return jsonify({"error": payload}), e.status

    @app.errorhandler(404)
    def _handle_404(e):
        return jsonify({"error": {"status": 404, "mensaje": "Recurso no encontrado."}}), 404

    @app.errorhandler(405)
    def _handle_405(e):
        return jsonify({"error": {"status": 405, "mensaje": "Metodo no permitido para esta ruta."}}), 405

    @app.errorhandler(Exception)
    def _handle_uncaught(e: Exception):
        current_app.logger.exception(e)
        payload = {"status": 500, "mensaje": "Error interno del servidor."}
        if current_app.config["DEBUG"]:
            payload["debug"] = {"excepcion": type(e).__name__, "mensaje": str(e)}
        return jsonify({"error": payload}), 500
