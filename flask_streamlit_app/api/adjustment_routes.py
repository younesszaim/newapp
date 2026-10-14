"""Routes Flask de création des ajustements."""

from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from api.adjustment_models import AdjustmentBatchRequest
from api.adjustment_service import (
    create_adjustment_block,
    delete_adjustment_block,
    get_adjustment_registry,
    get_latest_active_adjustment_before,
)
from api.database import database_connection

adjustment_blueprint = Blueprint("adjustments", __name__, url_prefix="/api")


@adjustment_blueprint.get("/asofdates/<asofdate>/latest-active-adjustment")
def latest_active_adjustment(asofdate: str):
    """Retourne le dernier ajustement actif avant une date.
    ---
    tags: [Ajustements]
    parameters:
      - name: asofdate
        in: path
        required: true
        type: string
        format: date
        example: '2026-10-10'
    responses:
      200:
        description: Bloc actif le plus récent, ou null si aucun bloc antérieur.
      400:
        description: Date invalide (format attendu YYYY-MM-DD).
      500:
        description: Base PostgreSQL indisponible.
    """

    try:
        selected_asofdate = date.fromisoformat(asofdate)
    except ValueError:
        return jsonify(error="L'asofdate doit respecter le format YYYY-MM-DD."), 400

    with database_connection() as connection:
        block = get_latest_active_adjustment_before(connection, selected_asofdate)
    if block is None:
        return jsonify(None), 200
    return jsonify(block.model_dump(mode="json", by_alias=True)), 200


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

    with database_connection() as connection:
        blocks = get_adjustment_registry(connection)
    return jsonify([
        block.model_dump(mode="json", by_alias=True)
        for block in blocks
    ])


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
        adjustment_request = AdjustmentBatchRequest.model_validate(payload)
    except ValidationError as error:
        return jsonify(error=_validation_message(error)), 400

    with database_connection() as connection:
        result = create_adjustment_block(connection, adjustment_request)
    return jsonify(result.model_dump(mode="json", by_alias=True)), 201


def _validation_message(error: ValidationError) -> str:
    """Transforme la première erreur Pydantic en message API lisible."""

    detail = error.errors(include_url=False)[0]
    field = ".".join(str(part) for part in detail["loc"])
    error_type = detail["type"]
    if error_type == "missing":
        return f"Le champ '{field}' est obligatoire."
    if error_type == "extra_forbidden":
        return f"Le champ '{field}' n'est pas autorisé."
    if error_type in {"too_short", "too_long", "list_type"}:
        return "Un ajustement doit contenir entre 1 et 100 lignes."
    return f"La valeur du champ '{field}' est invalide."


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

    with database_connection() as connection:
        delete_adjustment_block(connection, parsed_id)
    return "", 204
