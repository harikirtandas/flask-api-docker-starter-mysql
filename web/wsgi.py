from flask import Flask

# Misma idea que el @app.get("/") que tenia la API: solo que ahora vive en su
# propio proceso/puerto, separado de la API. Placeholder para una fase futura
# donde esto crece a una app Flask con rutas/templates reales -- por eso es
# una app Flask (dinamica) y no un servidor puramente estatico tipo nginx.
app = Flask(__name__, static_folder=".", static_url_path="")


@app.get("/")
def index():
    return app.send_static_file("index.html")
