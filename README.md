# flask-api-docker-starter-mysql

Plantilla de GitHub para arrancar una **API REST en Python** con **Flask** y
**mysql-connector-python**, dockerizada con **MySQL 8**, en cualquier maquina,
con un solo comando.

Es el hermano Python de la familia de starters
[`php-api-docker-starter-apache-mysql`](../php-api-docker-starter-apache-mysql):
misma filosofia (JSON, CORS, manejo central de errores, slice demo descartable
sobre el mismo esqueleto Docker/Makefile), pero con autenticacion por **JWT**
en vez de token opaco, y un cliente generico para consumir catalogos externos
de solo lectura.

**Backend y frontend corren en servicios/puertos separados**, a proposito: la
API (`app`) no sirve nada de HTML/JS, y el cliente demo vive en `web/`,
corrido por una app Flask minima aparte. La unica comunicacion entre ambos es
HTTP contra la API (ver "Arquitectura" y "CORS" mas abajo).

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (o Docker Engine + Compose plugin) corriendo.
- [GitHub CLI](https://cli.github.com/) (`gh`) para crear proyectos nuevos desde la terminal. Alternativa: boton **"Use this template"** en GitHub.

## Crear un proyecto nuevo desde este template

```bash
gh repo create mi-api --template harikirtandas/flask-api-docker-starter-mysql --private --clone
cd mi-api
make install
```

Al terminar:

- API -> **http://localhost:8080**
- Cliente demo (`web/`, otro contenedor/puerto) -> **http://localhost:8082**
- Adminer (cliente web de MySQL) -> **http://localhost:8081**

A diferencia del hermano PHP, aca no hace falta un paso de instalacion aparte
antes de `docker compose up`: las dependencias de `requirements.txt` se
instalan **durante el build de la imagen**, no en un volumen bind-mounteado.
`make install` simplemente hace `docker compose up -d --build`.

## Arquitectura

**Backend y frontend son dos servicios Docker independientes**, cada uno con
su propio puerto, comunicados solo por HTTP contra la API. A eso se suman
MySQL y Adminer:

| Servicio  | Imagen                           | Rol                                                                                    |
| --------- | -------------------------------- | -------------------------------------------------------------------------------------- |
| `app`     | build propio, `python:3.12-slim` | Solo API: Flask (servidor de desarrollo) escuchando en :5000. Publica `APP_PORT` (default 8080). |
| `web`     | build propio, `python:3.12-slim` | Cliente demo (`web/`): una app Flask minima que sirve `index.html`/`css/`/`js/`. No es un servidor puramente estatico (no hace falta nginx) — es Flask de verdad, lista para crecer con rutas/templates propias mas adelante. Publica `WEB_PORT` (default 8082). |
| `mysql`   | `mysql:8`                        | Base de datos, volumen persistente `mysql-data` + healthcheck.                         |
| `adminer` | `adminer`                        | Cliente web de MySQL, publica `ADMINER_PORT` (default 8081).                           |

`./src` se monta como bind mount en `app`, y ya **no tiene ningun archivo de
frontend adentro** (se movio a `web/`). `./web` se monta, de solo lectura en
la practica, en `web` — ambos con auto-reload del dev server de Flask
(`FLASK_DEBUG=1`).

## Estructura del repo

```
.
├── src/
│   ├── requirements.txt
│   ├── wsgi.py                 # entry point: from app import create_app
│   ├── config.py               # Config: lee TODO de os.environ, sin secretos hardcodeados
│   └── app/                    # SOLO la API
│       ├── __init__.py          # create_app(): registra blueprints, CORS, errores
│       ├── core/
│       │   ├── database.py      # conexion mysql-connector-python por request (flask.g)
│       │   ├── errors.py        # ApiException + manejo central de errores -> JSON
│       │   ├── cors.py           # headers CORS + preflight OPTIONS
│       │   ├── auth.py            # JWT: generar_token(), usuario_actual(), revocar_token_actual()
│       │   └── external_catalog.py  # cliente generico para catalogos externos de solo lectura
│       ├── models/                # Usuario, TokenRevocado, Nota  (slice demo)
│       └── routes/                # blueprints: ping, auth, notas, catalogo  (slice demo)
└── web/                         # SOLO el frontend, otro puerto
    ├── requirements.txt          # Flask==3.1.*  (nada de mysql-connector-python/PyJWT)
    ├── wsgi.py                   # app Flask minima: sirve index.html/css/js
    ├── index.html                # cliente demo (login/registro + CRUD de notas)
    ├── css/app.css
    └── js/
        ├── api.js                # wrapper de fetch, agnostico al dominio
        └── app.js                # cliente demo que usa api.js (descartable)
```

**Nota de alcance**: este desacople no toca los blueprints de `app/routes/`
todavia — es un cambio aparte, pendiente para mas adelante.

## El slice demo (descartable)

Un vertical slice completo para probar de punta a punta que Flask, el
autoloading de blueprints, MySQL y la auth JWT funcionan juntos. **En un
proyecto real se borra entero** (`Auth` mas alla de `login`/`me` si no aplica,
`Nota` en `models/`/`routes/`, la tabla de `notas` del schema, y todo `web/`)
y se reemplaza por el dominio propio. Lo que se conserva es todo `app/core/`.

| Metodo        | Ruta                           | Auth | Que hace                                                 |
| ------------- | ------------------------------ | ---- | -------------------------------------------------------- |
| `GET`         | `/api/ping`                    | no   | `{ "pong": true, "hora": ... }`                          |
| `GET`         | `/api/health/db`               | no   | `SELECT 1` contra MySQL                                  |
| `POST`        | `/api/auth/register`           | no   | `{ nombre, email, password }` -> 201 usuario             |
| `POST`        | `/api/auth/login`              | no   | `{ email, password }` -> `{ token, expira, usuario }`    |
| `GET`         | `/api/auth/me`                 | si   | usuario dueno del token                                  |
| `POST`        | `/api/auth/logout`             | si   | revoca el token (204)                                    |
| `GET`         | `/api/notas`                   | si   | lista las notas del usuario                              |
| `POST`        | `/api/notas`                   | si   | `{ titulo, cuerpo }` -> 201 + `Location`                 |
| `GET`         | `/api/notas/{id}`              | si   | una nota                                                 |
| `PUT`/`PATCH` | `/api/notas/{id}`              | si   | reemplaza -> 200                                         |
| `DELETE`      | `/api/notas/{id}`              | si   | -> 204                                                   |
| `GET`         | `/api/catalogo/{recurso}`      | no   | proxy de juguete hacia `EXTERNAL_API_BASE_URL/{recurso}` |
| `GET`         | `/api/catalogo/{recurso}/{id}` | no   | idem, por id                                             |

Usuario demo: **`demo@demo.test` / `secret`**.

### Probar con curl

```bash
# login
TOKEN=$(curl -s -X POST localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@demo.test","password":"secret"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')

# listar notas
curl -s localhost:8080/api/notas -H "Authorization: Bearer $TOKEN"

# crear
curl -s -X POST localhost:8080/api/notas \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"titulo":"Hola","cuerpo":"desde curl"}' -i

# editar (PATCH, reemplazo completo)
curl -s -X PATCH localhost:8080/api/notas/1 \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"titulo":"Editada","cuerpo":"nuevo cuerpo"}'

# borrar
curl -s -X DELETE localhost:8080/api/notas/3 -H "Authorization: Bearer $TOKEN" -i

# logout (revoca el token: reusarlo despues da 401)
curl -s -X POST localhost:8080/api/auth/logout -H "Authorization: Bearer $TOKEN" -i
```

## Respuestas y errores

Mismo contrato de error que los hermanos PHP, a proposito (un cliente o una
coleccion de Bruno que ya sabe leer uno los sabe leer todos):

```json
{
  "error": {
    "status": 422,
    "mensaje": "Datos invalidos.",
    "errores": { "email": "Formato invalido" }
  }
}
```

Los blueprints tiran `app.core.errors.ApiException` para cortar con un error:

```python
raise ApiException(404, "Nota no encontrada.")
raise ApiException.validacion({"email": "Formato invalido"})
```

Con `APP_DEBUG=1`, un 500 no controlado incluye `error.debug` con la excepcion
y el mensaje. En `0`, solo un mensaje generico (y queda logueado igual con
`current_app.logger.exception`).

## Validacion (JSON Schema)

Los campos de cada request (`register`, `notas`) se validan contra un JSON
Schema, no a mano campo por campo, con librerias equivalentes de cada lado:

- **Backend**: [`jsonschema-rs`](https://pypi.org/project/jsonschema-rs/)
  (bindings Python de un validador Rust, rapido). Wrapper:
  `App.core.validator.validar(nombre_schema, datos)`. Schemas en
  `src/app/schemas/*.json` (uno por recurso).
- **Frontend**: [Ajv](https://ajv.js.org/) (build de navegador via CDN, sin
  build step). Wrapper: `web/js/validar.js` (`Validador.validar(...)`).
  Schemas en `web/schemas/*.json` — **copias a mano** de los del backend
  (no hay build compartido entre los dos proyectos/procesos); si divergen,
  gana el backend, esto solo da feedback instantaneo antes de la ida y
  vuelta de red.

Ambos lados traducen los errores de su libreria al mismo formato
`{ campo: mensaje }` de siempre — el contrato de un 422 no cambia:

```python
# backend
validar("auth_register", {"nombre": nombre, "email": email, "password": password})
```

```js
// frontend, antes de llamar a la API
const invalido = await Validador.validar('auth_register', { nombre, email, password });
if (invalido) return mostrarError(errorAuth, invalido);
```

Un campo ausente dispara `required` (mensaje `"Requerido."`); presente pero
mal tipado dispara `type`/`minLength`/`maxLength` (mapeo keyword -> texto en
espanol en `validator.py`/`validar.js`, mantenido igual en los dos lados a
mano). Detalle no obvio de `jsonschema-rs`: el keyword `required` no da un
`instance_path` util (apunta al objeto entero, no al campo faltante) — el
nombre del campo sale de `error.kind.as_dict()["property"]`. Ajv tiene el
mismo caso, con `error.params.missingProperty`.

## Autenticacion (JWT)

`app/core/auth.py`:

- `generar_token(usuario)`: firma un JWT (`HS256`, secreto `JWT_SECRET`) con
  `sub` (id de usuario), `jti` (uuid unico) y `exp` (`JWT_TTL_HORAS`, default
  7 dias).
- `usuario_actual()`: guard que se llama como **primera linea** de cada
  endpoint protegido (sin decorator/middleware, a proposito: queda a la vista
  que endpoint pide sesion con solo leer su primera linea). Valida firma y
  vencimiento, chequea que el `jti` no este en la lista negra, y resuelve el
  usuario.
- `revocar_token_actual()`: logout. El JWT en si es sin estado; revocarlo
  antes de su `exp` natural requiere guardar su `jti` en la tabla
  `tokens_revocados` hasta que venza solo (no hay job de limpieza en este
  starter, una fila vieja es inofensiva aunque no se borre).

## Cliente de catalogos externos de solo lectura

`app/core/external_catalog.py` (`ExternalCatalogClient`) es generico y
reusable: sirve para consumir cualquier API externa de solo lectura protegida
por un header de API key (ej. la "API del Profesor" de un proyecto con
catalogo centralizado). Deliberadamente **no expone POST/PUT/DELETE**.

Config (variables de entorno):

```bash
EXTERNAL_API_BASE_URL=https://api-ejemplo.test/api/v1
EXTERNAL_API_KEY_HEADER=Grupo-Access-Key
EXTERNAL_API_KEY=<clave-asignada>
EXTERNAL_API_CACHE_TTL=30
```

Sin `EXTERNAL_API_BASE_URL` configurada, `GET /api/catalogo/*` responde `501`
en vez de romper `make install` para quien no necesita esta pieza. Maneja
`401` (key invalida) y `429` (rate limit) del lado externo devolviendolos tal
cual al cliente propio, y loguea cualquier error de conexion.

Para un proyecto real con dos catalogos concretos (ej. `/lenguajes` y
`/tecnologias`), lo mas simple es un blueprint por catalogo, cada uno con
**solo** el verbo `GET`, usando esta misma clase — ver el comentario al
principio de `app/routes/catalogo.py`.

## CORS

Backend (`app`, puerto `APP_PORT`) y frontend (`web`, puerto `WEB_PORT`) son
dos origenes distintos para el navegador (mismo host, pero **puerto**
distinto ya cuenta como otro origen). `app/core/cors.py` agrega los headers
CORS a toda respuesta y contesta el preflight `OPTIONS` con 204 antes de
llegar a cualquier blueprint. El origen permitido sale de `CORS_ORIGIN`, que
**hay que mantener sincronizado con `WEB_PORT`** (default
`http://localhost:8082`); si cambia uno, cambia el otro. Nota: esto es
puramente para el navegador — un cliente movil (Android) no aplica politica
de mismo origen y no le afecta este valor.

## Configuracion

Todo se lee de variables de entorno (`config.py`, inyectadas por
`docker-compose.yml`), nunca de un `.env` parseado dentro del contenedor:

```bash
APP_PORT=8080
WEB_PORT=8082
ADMINER_PORT=8081
APP_DEBUG=1
CORS_ORIGIN=http://localhost:8082
JWT_SECRET=cambiame-en-produccion-min-32-caracteres
JWT_TTL_HORAS=168
DB_DATABASE=app
DB_USERNAME=app
DB_PASSWORD=secret
EXTERNAL_API_BASE_URL=
EXTERNAL_API_KEY_HEADER=Grupo-Access-Key
EXTERNAL_API_KEY=
EXTERNAL_API_CACHE_TTL=30
```

Para overridear cualquiera de estas, crear un `.env` en la raiz del proyecto
(gitignoreado) — `docker-compose.yml` ya tiene fallbacks para todas.

Si cambia `APP_PORT`, hay que actualizar tambien la linea
`window.API_BASE_URL = ...` en `web/index.html` — es la unica que conecta el
cliente demo con la API.

## Comandos (Makefile)

| Comando                           | Que hace                                                                                                                           |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `make install`                    | Levanta los cuatro contenedores (`app`, `web`, `mysql`, `adminer`), rebuildeando las imagenes si hace falta. Una sola vez por proyecto, o cuando cambia algun `requirements.txt`.  |
| `make up` / `make down`           | Levanta / apaga. `down` **no borra datos**.                                                                                        |
| `make restart`                    | Reinicia sin rebuildear.                                                                                                           |
| `make shell`                      | `bash` dentro del contenedor `app`.                                                                                                |
| `make db-shell`                   | Cliente `mysql` conectado a la base del proyecto.                                                                                  |
| `make logs`                       | Sigue los logs.                                                                                                                    |
| `make db-import FILE=x.sql`       | Aplica un `.sql` a la base ya corriendo, sin recrear el volumen.                                                                   |
| `make fresh`                      | Borra `mysql-data` y reaplica `docker/mysql/init/*.sql`. Pide confirmacion.                                                        |
| `make pip CMD="install requests"` | pip dentro del contenedor corriendo (para probar rapido; sumarlo a `requirements.txt` y `make install` para que quede permanente). |

## Agregar tablas sin perder datos

`docker/mysql/init/*.sql` solo corre en el primer arranque del volumen. Para
sumar una tabla a un proyecto con datos ya cargados:

1. Guardar el archivo numerado: `docker/mysql/init/02-nombre.sql` (con
   `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE`).
2. `make db-import FILE=docker/mysql/init/02-nombre.sql`

## Arrancar un proyecto real

1. `gh repo create mi-api --template harikirtandas/flask-api-docker-starter-mysql --private --clone && cd mi-api`
2. Reemplazar `docker/mysql/init/01-schema.sql` por el schema real.
3. Borrar el slice demo: `Nota` en `models/`/`routes/`, la ruta demo de
   `catalogo.py` (o adaptarla a los dos catalogos reales), y todo `web/`.
   `register`/`login`/`me`/`logout` de `auth.py` suelen quedar, adaptados a
   las columnas reales de `usuarios`.
4. Conservar todo `app/core/`.
5. `make install`.
