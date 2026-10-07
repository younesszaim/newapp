"""Point d'entrée minimal de l'API Flask.

Exemple : GET http://127.0.0.1:5000/api/health
Réponse : {"status": "ok"}
"""

from flask import Flask, jsonify


def create_app() -> Flask:
    """Construit l'application Flask afin de faciliter les futurs tests."""

    app = Flask(__name__)

    @app.get("/api/health")
    def health() -> tuple[dict[str, str], int]:
        return jsonify(status="ok"), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
