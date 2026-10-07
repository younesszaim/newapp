"""Point d'entrée minimal de l'API Flask.

Exemple : GET http://127.0.0.1:5000/api/health
Réponse : {"status": "ok"}
"""

from flask import Flask, jsonify
from flasgger import Swagger

from api.context_routes import context_blueprint
from api.lcr_routes import lcr_blueprint
from api.adjustment_routes import adjustment_blueprint


def create_app() -> Flask:
    """Construit l'application Flask afin de faciliter les futurs tests."""

    app = Flask(__name__)
    app.config["SWAGGER"] = {
        "title": "LCR Adjustments API",
        "uiversion": 3,
    }
    Swagger(
        app,
        template={
            "info": {
                "title": "LCR Adjustments API",
                "description": "API Flask de gestion des ajustements LCR.",
                "version": "1.0.0",
            }
        },
    )
    app.register_blueprint(context_blueprint)
    app.register_blueprint(lcr_blueprint)
    app.register_blueprint(adjustment_blueprint)

    @app.get("/api/health")
    def health() -> tuple[dict[str, str], int]:
        """Vérifie que l'API Flask répond.
        ---
        tags:
          - Système
        responses:
          200:
            description: L'API est disponible.
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: ok
        """
        return jsonify(status="ok"), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
