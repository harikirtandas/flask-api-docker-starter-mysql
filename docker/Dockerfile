FROM python:3.12-slim

# mysql-connector-python es pure-python (no libmysqlclient-dev necesario, a
# diferencia de mysqlclient/PyMySQL con extension C). No hace falta gcc ni
# headers de sistema para el set de dependencias de este starter.
WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# el codigo real llega por el bind mount (./src:/app en docker-compose): esto
# es solo para que la imagen tenga algo copiado si se corre sin el mount (por
# ejemplo, un build de CI). En desarrollo el bind mount pisa este COPY.
COPY src/ .

EXPOSE 5000

# servidor de desarrollo de Flask: alcanza para el alcance de este starter
# (igual que los hermanos PHP corren con mod_php sin tunear para produccion).
# Para produccion real, reemplazar por gunicorn ("gunicorn -b 0.0.0.0:5000 wsgi:app").
CMD ["flask", "--app", "wsgi:app", "run", "--host=0.0.0.0", "--port=5000"]
