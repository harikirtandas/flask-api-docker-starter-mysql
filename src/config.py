import os


def _bool(valor, default=False):
    if valor is None:
        return default
    return valor.strip().lower() not in ("", "0", "false", "no")


class Config:
    """Config simple, sin secretos hardcodeados: todo viene de variables de
    entorno que docker-compose inyecta (ver environment: en docker-compose.yml).
    Nada de esto se lee de un .env dentro del contenedor a proposito -- mismo
    criterio que App\\Core\\Database::connection() en los hermanos PHP
    (os.environ, nunca un .env parseado a mano)."""

    DEBUG = _bool(os.environ.get("APP_DEBUG"), default=False)
    CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")

    # HS256 recomienda un secreto de al menos 32 bytes (RFC 7518 3.2); uno mas
    # corto no rompe nada pero PyJWT tira InsecureKeyLengthWarning en cada
    # encode/decode. El default de abajo es solo para que "make install"
    # funcione sin configurar nada: cambiarlo siempre en un proyecto real.
    JWT_SECRET = os.environ.get("JWT_SECRET", "cambiame-en-produccion-min-32-caracteres")
    JWT_TTL_HORAS = int(os.environ.get("JWT_TTL_HORAS", "168"))  # 7 dias

    DB_HOST = os.environ.get("DB_HOST", "mysql")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_DATABASE = os.environ.get("DB_DATABASE", "app")
    DB_USERNAME = os.environ.get("DB_USERNAME", "app")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "secret")

    # cliente generico de catalogos externos de solo lectura (app/core/external_catalog.py).
    # Sin EXTERNAL_API_BASE_URL configurada, el blueprint de catalogo demo
    # responde 501 en vez de romper "make install" para quien no lo necesita.
    EXTERNAL_API_BASE_URL = os.environ.get("EXTERNAL_API_BASE_URL", "").rstrip("/")
    EXTERNAL_API_KEY_HEADER = os.environ.get("EXTERNAL_API_KEY_HEADER", "Grupo-Access-Key")
    EXTERNAL_API_KEY = os.environ.get("EXTERNAL_API_KEY", "")
    EXTERNAL_API_CACHE_TTL = int(os.environ.get("EXTERNAL_API_CACHE_TTL", "30"))
