"""Exceptions métier et réponses d'erreur communes à toute l'API."""

from flask import Flask, jsonify
from psycopg2 import DatabaseError


class ApplicationError(Exception):
    """Erreur contrôlée pouvant être présentée au client HTTP."""

    status_code = 500


class ConfigurationError(ApplicationError):
    """Configuration serveur absente ou invalide."""


class AdjustmentNotFoundError(ApplicationError):
    status_code = 404


class AdjustmentConflictError(ApplicationError):
    status_code = 409


class TradeNumberGenerationError(ApplicationError):
    """Échec exceptionnel après plusieurs collisions de TradeNo."""


def register_error_handlers(app: Flask) -> None:
    """Enregistre une réponse JSON uniforme pour les erreurs connues."""

    @app.errorhandler(ApplicationError)
    def handle_application_error(error: ApplicationError):
        return jsonify(error=str(error)), error.status_code

    @app.errorhandler(DatabaseError)
    def handle_database_error(_error: DatabaseError):
        return jsonify(error="Une erreur PostgreSQL est survenue."), 500
