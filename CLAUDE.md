# flask-api-docker-starter-mysql

- **Backend y frontend corren en servicios/puertos separados, a proposito**:
  `app` (la API) ya no sirve nada de HTML/JS/CSS — eso se movio a `web/`
  (fuera de `src/`), corrido por una app Flask minima aparte, en su propio
  contenedor/puerto (`WEB_PORT`, default 8082). Motivo: backend y frontend
  deben poder ejecutarse, deployarse y escalar de forma independiente, con la
  API como unico medio de comunicacion — antes, Flask servia `static/` y la
  API desde el mismo puerto. No es nginx: es una app Flask de verdad (por eso
  "dinamica" y no un servidor puramente estatico), aunque hoy solo sirva los
  archivos de `web/` tal cual — placeholder para crecer con rutas/templates
  propias en una fase futura. Consecuencia directa: `web/js/api.js` ya NO
  puede asumir mismo origen (`BASE = '/api'` relativo); lee
  `window.API_BASE_URL`, seteada en un `<script>` de `web/index.html` ANTES
  de cargar `api.js`. Si cambia `APP_PORT`, hay que actualizar esa linea Y
  `CORS_ORIGIN` (ver bullet de CORS). **Nota de alcance**: este cambio no
  toca los blueprints de `app/routes/` — queda pendiente como paso aparte.
- **Validacion de body con JSON Schema, no a mano.** Backend:
  `jsonschema-rs` (bindings Python de un validador Rust) via
  `app.core.validator.validar(nombre_schema, datos)`, schemas en
  `src/app/schemas/*.json`. Frontend: Ajv (build de navegador por CDN, sin
  build step) via `web/js/validar.js`, schemas en `web/schemas/*.json`
  **copiados a mano** de los del backend (dos proyectos/procesos separados,
  sin build compartido — si divergen, gana el backend). Ambos traducen los
  errores de su libreria al mismo `{ campo: mensaje }` de siempre; el
  contrato de un 422 no cambia. El trim/normalizacion de strings sigue
  siendo responsabilidad de cada ruta/handler, ANTES de llamar a validar().
  Gotcha de `jsonschema-rs`: el keyword `required` no trae un
  `instance_path` util para el campo faltante (apunta al objeto entero) — el
  nombre sale de `error.kind.as_dict()["property"]`; Ajv tiene el mismo caso
  via `error.params.missingProperty`. Nueva dependencia de pip:
  `jsonschema-rs` en `src/requirements.txt` — hace falta rebuildear la imagen
  (`make install` o `docker compose up -d --build`) para bajarla, un simple
  `docker compose up` no alcanza.
- Hermano Python de la familia de starters `php-api-docker-starter-apache-mysql`
  / `php-api-rustica-docker-starter-apache-mysql` / etc. **Mismo contrato de
  error JSON**, mismo Makefile (nombres de targets), mismo esquema de
  variables de entorno (`APP_PORT`, `APP_DEBUG`, `CORS_ORIGIN`, `DB_*`), mismo
  patron de slice demo descartable. Difiere donde el ecosistema lo obliga:
  Flask no corre bajo Apache/mod_php, asi que no hay `.htaccess` ni fix de
  reinyeccion del header `Authorization` (Flask lo recibe intacto siempre).
- **Diferencia de fondo con los hermanos PHP: auth por JWT, no token opaco en
  tabla.** El JWT es sin estado (la firma alcanza para validarlo sin ir a la
  base) salvo por logout: revocar antes del `exp` natural requiere una lista
  negra minima (`tokens_revocados`, solo `jti` + `expira_en`). No hay job de
  limpieza; una fila vieja es inofensiva.
- **No hace falta un `make install` en dos pasos como el hermano PHP.** Las
  dependencias de `requirements.txt` se instalan durante el `docker build`
  (`COPY requirements.txt` + `pip install` ANTES del bind mount), no en un
  volumen bind-mounteado como `vendor/` en PHP. Consecuencia: si se agrega una
  dependencia nueva a `requirements.txt`, hace falta `make install` (rebuildea
  la imagen) o `docker compose build`; un simple `docker compose up` no la va
  a instalar sola.
- **Conexion a MySQL: una por request via `flask.g`**, NO un pool
  (`app/core/database.py`). `get_db()` la abre la primera vez que se pide
  dentro del request y `close_db()` (registrado como `teardown_appcontext` en
  `create_app()`) la cierra al final. Deliberado: para el alcance de un
  starter, un pool agrega superficie de fallas (agotamiento, conexiones
  zombies) sin beneficio real; es el patron que la propia documentacion de
  Flask recomienda para recursos de request.
- **`app/__init__.py` es la unica fabrica de la app** (`create_app()`):
  registra CORS, manejo de errores y los 4 blueprints del slice demo, en ese
  orden. `wsgi.py` en la raiz de `src/` es el unico entry point (`flask --app
  wsgi:app run`, ver `docker/Dockerfile`).
- **Blueprints en vez de un router propio**: a diferencia de los hermanos PHP
  (que traen `App\Core\Router` hecho a mano porque PHP plano no tiene nada
  built-in), Flask ya resuelve rutas con parametros tipados (`<int:id_>`) y
  multiples verbos por regla (`methods=["PUT", "PATCH"]`) sin reinventar nada.
  No hay equivalente a `Router.php` en este starter a proposito.
- **Guards de auth explicitos, sin decorator/middleware**: cada endpoint
  protegido llama `usuario_actual()` como primera linea del cuerpo de la
  funcion (`app/core/auth.py`), igual que `Auth::usuarioActual($request)` en
  los hermanos PHP. Se eligio a proposito sobre un decorator `@requiere_auth`
  para que quede a la vista, leyendo solo la primera linea de cada funcion,
  que endpoint pide sesion y cual no — mismo criterio de legibilidad de toda
  la familia.
- **`app/core/errors.py`**: `ApiException(status, mensaje, errores=None)` +
  `register_error_handlers(app)` capturando `ApiException`, 404, 405 y
  `Exception` generico. Traduce todo a
  `{ "error": { "status", "mensaje", "errores"? } }` — **el mismo shape que
  `App\Core\ApiException` de los hermanos PHP**, decision deliberada para que
  un cliente (o una coleccion de Bruno) que sabe leer el error de un starter
  de la familia lo sepa leer de todos.
- **CORS manual (`app/core/cors.py`), sin `flask-cors`**: mismo criterio que
  los hermanos PHP setean los headers a mano en `index.php` en vez de sumar
  una libreria solo para esto. `before_request` corta el preflight `OPTIONS`
  con 204 antes de tocar cualquier blueprint; `after_request` agrega los
  headers a toda respuesta. `CORS_ORIGIN` ya cumple su funcion real (no es
  cosmetico): `app` y `web` corren en puertos distintos, asi que para el
  navegador son origenes distintos de verdad, default `http://localhost:8082`
  (el puerto de `web`).
- **`app/core/external_catalog.py` (`ExternalCatalogClient`) es la pieza
  nueva sin equivalente en los hermanos PHP**: cliente generico y reusable
  para consumir un catalogo externo de solo lectura protegido por header de
  API key (pensado para el caso "API centralizada de otro equipo", tipo
  catalogo de tecnologias/lenguajes de un proyecto con integracion externa).
  Cachea en memoria del proceso por un TTL corto (`EXTERNAL_API_CACHE_TTL`) y
  traduce 401/429/errores de conexion del lado externo a `ApiException`
  propias. **No expone POST/PUT/DELETE** a proposito: si el catalogo remoto es
  de solo lectura, que el cliente ni siquiera tenga el metodo es la forma mas
  simple de garantizar que nadie escriba ahi por accidente.
- **`app/routes/catalogo.py` es un demo generico parametrizado
  (`/api/catalogo/<recurso>`), no el dominio real.** Sin
  `EXTERNAL_API_BASE_URL` configurada responde `501` en vez de romper `make
  install` para quien no necesita esta pieza. El comentario al principio del
  archivo documenta como pasar a dos blueprints concretos con un catalogo real
  (solo GET, nunca escritura).
- **Passwords: `werkzeug.security` (`generate_password_hash` /
  `check_password_hash`), metodo `pbkdf2:sha256` forzado explicitamente.**
  Werkzeug soporta tambien `scrypt`, pero ese metodo requiere el paquete
  opcional `scrypt` instalado aparte — no esta en `requirements.txt`, asi que
  dejar el metodo default (que puede ser scrypt segun version) rompería la
  verificacion en runtime. El hash del usuario demo en
  `01-schema.sql` fue generado a mano con
  `generate_password_hash('secret', method='pbkdf2:sha256')`; si se regenera,
  hay que mantener el mismo method.
- **`requirements.txt` fijado a mayor de version (`Flask==3.1.*`,
  `mysql-connector-python==9.*`, etc.), no a un patch exacto.** Se resuelve en
  cada build de imagen (no hay lockfile tipo `composer.lock`); si hace falta
  reproducibilidad estricta, pinnear versiones exactas y considerar sumar
  `pip freeze > requirements.lock.txt`.
- **`mysql-connector-python` usa placeholders `%s`, no `:nombre` como PDO.**
  Toda query parametrizada en `app/models/*.py` sigue esa sintaxis; copiar un
  patron de los hermanos PHP sin ajustar el placeholder rompe en runtime con
  un error de sintaxis SQL poco obvio.
- **Vertical slice demo, descartable como conjunto**: `ping.py` (ping +
  health/db), `auth.py` (`register`/`login`/`me`/`logout`) + `Usuario` +
  `TokenRevocado`, `notas.py` + `Nota` (CRUD con los 5 verbos, filtrado por
  usuario), el schema `01-schema.sql` (`usuarios`/`tokens_revocados`/`notas` +
  usuario demo `demo@demo.test`/`secret`), y el cliente demo, que ahora vive
  entero en `web/` (fuera de `src/`, otro servicio/puerto — ver primer bullet
  de este archivo). En un proyecto real se borra entero; se conserva
  `app/core/`.
