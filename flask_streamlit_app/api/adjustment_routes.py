"""Routes Flask de création des ajustements."""

from datetime import date, datetime

from flask import Blueprint, jsonify, request
from psycopg2 import DatabaseError

from api.adjustment_service import create_adjustment_block, validate_adjustment_lines
from api.database import database_connection

adjustment_blueprint = Blueprint("adjustments", __name__, url_prefix="/api")


@adjustment_blueprint.post("/adjustments")
def create_adjustment():
    """Crée un bloc de plusieurs deals fictifs.
    ---
    tags:
      - Ajustements
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [asofdate, asofdateflowVersion, adjustments]
          properties:
            asofdate: {type: string, format: date}
            asofdateflowVersion: {type: string, format: date-time}
            adjustments:
              type: array
              minItems: 1
              maxItems: 100
              items:
                type: object
                required: [ldpImpactLcrReglementaire, ldpImpactLcrGestion]
    responses:
      201:
        description: Bloc créé dans une seule transaction.
      400:
        description: Corps JSON ou montants invalides.
      500:
        description: Échec de l'enregistrement PostgreSQL.
    """

    payload = request.get_json(silent=True) or {}
    try:
        asofdate = date.fromisoformat(payload["asofdate"])
        version = datetime.fromisoformat(payload["asofdateflowVersion"])
        lines = validate_adjustment_lines(payload.get("adjustments"))
    except (KeyError, TypeError, ValueError) as error:
        return jsonify(error=str(error) or "Requête invalide."), 400

    try:
        with database_connection() as connection:
            result = create_adjustment_block(connection, asofdate, version, lines)
        return jsonify(result), 201
    except (DatabaseError, RuntimeError):
        return jsonify(error="Impossible d'enregistrer l'ajustement."), 500
