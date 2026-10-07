"""Routes Flask du contexte date/version."""

from flask import Blueprint, jsonify
from psycopg2 import DatabaseError

from api.context_repository import list_asofdates
from api.database import database_connection

context_blueprint = Blueprint("context", __name__, url_prefix="/api")


@context_blueprint.get("/asofdates")
def get_asofdates():
    """Liste les dates d'arrêté disponibles.
    ---
    tags:
      - Contexte LCR
    responses:
      200:
        description: Dates triées de la plus récente à la plus ancienne.
        schema:
          type: array
          items:
            type: string
            format: date
          example: ["2026-10-05", "2026-10-04"]
      500:
        description: Configuration absente ou base indisponible.
    """

    try:
        with database_connection() as connection:
            return jsonify(list_asofdates(connection))
    except (DatabaseError, RuntimeError):
        return jsonify(error="Impossible de charger les dates d'arrêté."), 500
