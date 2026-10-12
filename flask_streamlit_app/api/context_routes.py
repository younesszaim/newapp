"""Routes Flask du contexte date/version."""

from datetime import date

from flask import Blueprint, jsonify

from api.context_repository import list_asofdates, list_versions
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

    with database_connection() as connection:
        return jsonify(list_asofdates(connection))


@context_blueprint.get("/asofdates/<asofdate>/versions")
def get_versions(asofdate: str):
    """Liste les versions d'une date d'arrêté.
    ---
    tags:
      - Contexte LCR
    parameters:
      - name: asofdate
        in: path
        required: true
        type: string
        format: date
        example: "2026-10-05"
    responses:
      200:
        description: Versions triées de la plus récente à la plus ancienne.
        schema:
          type: array
          items:
            type: string
            format: date-time
          example: ["2026-10-06T15:30:00"]
      400:
        description: La date n'utilise pas le format YYYY-MM-DD.
      500:
        description: Configuration absente ou base indisponible.
    """

    try:
        parsed_asofdate = date.fromisoformat(asofdate)
    except ValueError:
        return jsonify(error="La date doit utiliser le format YYYY-MM-DD."), 400

    with database_connection() as connection:
        return jsonify(list_versions(connection, parsed_asofdate))
