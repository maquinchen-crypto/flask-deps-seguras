import os

from flask import Flask, request
from markupsafe import escape

app = Flask(__name__)


@app.route("/hello")
def hello():
    name = request.args.get("name", "mundo")
    # escape() evita XSS reflejado: el parámetro vuelve al navegador como texto
    #return f"Hello, {escape(name)}!"
    return f"Hello, {name}!"


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # debug nunca fijo en True: se activa solo con FLASK_DEBUG=1 en local
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
