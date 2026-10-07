"""Route Flask du résumé LCR."""

from datetime import date, datetime

from flask import Blueprint, jsonify, request
from psycopg2 import DatabaseError

from api.database import database_connection
from api.lcr_service import build_lcr_summary

lcr_blueprint = Blueprint("lcr", __name__, url_prefix="/api")


@lcr_blueprint.get("/lcr-summary")
def get_lcr_summary():
    """Retourne le résumé LCR d'une date et d'une version.
    ---
    tags:
      - Résumé LCR
    parameters:
      - name: asofdate
        in: query
        required: true
        type: string
        format: date
        example: "2026-10-05"
      - name: version
        in: query
        required: true
        type: string
        format: date-time
        example: "2026-10-06T15:30:00"
    responses:
      200:
        description: Lignes agrégées et totaux LCR.
      400:
        description: Paramètre absent ou invalide.
      500:
        description: Base PostgreSQL indisponible.
    """

    try:
        asofdate = date.fromisoformat(request.args["asofdate"])
        version = datetime.fromisoformat(request.args["version"])
    except (KeyError, ValueError):
        return jsonify(error="Les paramètres asofdate et version sont invalides."), 400

    try:
        with database_connection() as connection:
            return jsonify(build_lcr_summary(connection, asofdate, version))
    except (DatabaseError, RuntimeError):
        return jsonify(error="Impossible de charger le résumé LCR."), 500
