.PHONY: install up down restart shell db-shell logs db-import fresh pip

install:
	@mkdir -p docker/mysql/init
	docker compose up -d --build
	@echo "App     -> http://localhost:$${APP_PORT:-8080}"
	@echo "Adminer -> http://localhost:$${ADMINER_PORT:-8081}"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

shell:
	docker compose exec app bash

db-shell:
	docker compose exec mysql sh -c 'mysql -u"$$MYSQL_USER" -p"$$MYSQL_PASSWORD" "$$MYSQL_DATABASE"'

logs:
	docker compose logs -f

db-import:
	@test -n "$(FILE)" || (echo "uso: make db-import FILE=dump.sql" && exit 1)
	@test -f "$(FILE)" || (echo "no existe el archivo: $(FILE)" && exit 1)
	docker compose exec -T mysql sh -c 'mysql -u"$$MYSQL_USER" -p"$$MYSQL_PASSWORD" "$$MYSQL_DATABASE"' < "$(FILE)"

fresh:
	@read -p "Esto borra TODOS los datos de mysql-data. Escribi 'yes' para continuar: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v; \
		docker compose up -d --build; \
	else \
		echo "Cancelado."; \
	fi

# instala/actualiza dependencias dentro del contenedor sin rebuildear la imagen
# entera. Util mientras se prueba un paquete nuevo; para que quede permanente
# hay que sumarlo a src/requirements.txt y correr "make install" (rebuildea).
pip:
	@test -n "$(CMD)" || (echo "uso: make pip CMD=\"install requests\"" && exit 1)
	docker compose exec app pip $(CMD)
