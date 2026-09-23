import time

import requests
from flask import current_app

from app.core.errors import ApiException

# Cliente generico y reusable para consumir un catalogo externo de SOLO
# LECTURA (una API centralizada que administra otro equipo/organizacion, ej.
# la "API del Profesor" del proyecto final: /lenguajes, /tecnologias). No es
# especifico de ningun dominio: cualquier proyecto de la familia que necesite
# consumir un catalogo ajeno por header de API key puede reusar esta clase tal
# cual, apuntando EXTERNAL_API_BASE_URL/KEY a lo que corresponda.
#
# Deliberadamente NO expone POST/PUT/DELETE: si el catalogo remoto es de solo
# lectura (como exige el proyecto final sobre /lenguajes y /tecnologias), la
# forma mas simple de garantizar que nadie escriba ahi por accidente es que el
# cliente ni siquiera tenga el metodo.
#
# Cachea en memoria del proceso por un TTL corto (EXTERNAL_API_CACHE_TTL,
# default 30s): evita pegarle a la API externa en cada request del cliente web
# sin necesitar una tabla de sincronizacion aparte. Si el proyecto real
# prefiere la otra estrategia que permite el enunciado (sincronizar una copia
# propia de forma periodica), esta clase se puede seguir usando igual desde el
# comando de sync, ignorando la cache.
class ExternalCatalogClient:
    def __init__(self):
        self._cache: dict[str, tuple[float, object]] = {}

    def _config(self):
        base_url = current_app.config["EXTERNAL_API_BASE_URL"]
        if not base_url:
            raise ApiException(
                501,
                "EXTERNAL_API_BASE_URL no esta configurada. "
                "Definila en el entorno para habilitar este catalogo.",
            )
        return base_url

    def listar(self, recurso: str, params: dict | None = None):
        return self._get(recurso, params)

    def obtener(self, recurso: str, id_: int | str):
        return self._get(f"{recurso}/{id_}")

    def _get(self, path: str, params: dict | None = None):
        base_url = self._config()
        cache_key = f"{path}?{sorted((params or {}).items())}"

        ttl = current_app.config["EXTERNAL_API_CACHE_TTL"]
        cacheado = self._cache.get(cache_key)
        if cacheado is not None and time.monotonic() - cacheado[0] < ttl:
            return cacheado[1]

        headers = {current_app.config["EXTERNAL_API_KEY_HEADER"]: current_app.config["EXTERNAL_API_KEY"]}

        try:
            resp = requests.get(f"{base_url}/{path}", headers=headers, params=params, timeout=5)
        except requests.RequestException as e:
            current_app.logger.error("Catalogo externo no respondio (%s): %s", path, e)
            raise ApiException(502, "El catalogo externo no esta disponible en este momento.")

        if resp.status_code == 401:
            current_app.logger.error("Catalogo externo rechazo la API key en %s", path)
            raise ApiException(401, "La API key configurada para el catalogo externo es invalida.")

        if resp.status_code == 429:
            current_app.logger.warning("Catalogo externo: rate limit excedido en %s", path)
            raise ApiException(429, "Se supero el limite de solicitudes al catalogo externo, intenta de nuevo en unos segundos.")

        if resp.status_code == 404:
            raise ApiException(404, "Elemento no encontrado en el catalogo externo.")

        if not resp.ok:
            current_app.logger.error("Catalogo externo devolvio %s en %s", resp.status_code, path)
            raise ApiException(502, "El catalogo externo devolvio un error inesperado.")

        datos = resp.json()
        self._cache[cache_key] = (time.monotonic(), datos)
        return datos
