"""Routes Flask de création des ajustements."""

from datetime import date, datetime
from uuid import UUID

from flask import Blueprint, jsonify, request
from psycopg2 import DatabaseError

from api.adjustment_service import (
    create_adjustment_block,
    delete_adjustment_block,
    get_adjustment_registry,
    validate_adjustment_lines,
)
from api.database import database_connection

adjustment_blueprint = Blueprint("adjustments", __name__, url_prefix="/api")


@adjustment_blueprint.get("/adjustments")
def list_adjustments():
    """Liste les blocs actifs et supprimés.
    ---
    tags: [Ajustements]
    responses:
      200:
        description: Blocs avec leurs lignes actives relues depuis completude_table.
      500:
        description: Base PostgreSQL indisponible.
    """

    try:
        with database_connection() as connection:
            return jsonify(get_adjustment_registry(connection))
    except (DatabaseError, RuntimeError):
        return jsonify(error="Impossible de charger le registre."), 500


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


@adjustment_blueprint.delete("/adjustments/<adjustment_id>")
def delete_adjustment(adjustment_id: str):
    """Supprime toutes les lignes d'un bloc.
    ---
    tags: [Ajustements]
    parameters:
      - name: adjustment_id
        in: path
        required: true
        type: string
        format: uuid
    responses:
      204:
        description: Lignes supprimées et bloc marqué DELETED.
      400:
        description: UUID invalide.
      404:
        description: Ajustement introuvable.
      409:
        description: Ajustement déjà supprimé ou incomplet.
    """

    try:
        parsed_id = UUID(adjustment_id)
    except ValueError:
        return jsonify(error="L'adjustment_id doit être un UUID valide."), 400

    try:
        with database_connection() as connection:
            delete_adjustment_block(connection, parsed_id)
        return "", 204
    except LookupError as error:
        return jsonify(error=str(error)), 404
    except ValueError as error:
        return jsonify(error=str(error)), 409
    except (DatabaseError, RuntimeError):
        return jsonify(error="Impossible de supprimer l'ajustement."), 500
