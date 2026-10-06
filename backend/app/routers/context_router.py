"""Routes permettant de choisir le contexte de reporting LCR."""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from psycopg2.extensions import connection as PostgreSQLConnection

from app.database import get_connection
from app.repositories.lcr_repository import get_asofdates, get_versions

router = APIRouter(tags=["Contexte de reporting"])

# Annotated explique à FastAPI qu'il doit appeler get_connection() et injecter
# le résultat dans le paramètre connection de la route.
DatabaseConnection = Annotated[PostgreSQLConnection, Depends(get_connection)]


@router.get("/asofdates", response_model=list[date])
def list_asofdates(connection: DatabaseConnection) -> list[date]:
    """Liste les Asofdates disponibles dans la table des trades.

    Exemple JSON renvoyé à Angular :
        ["2026-10-05", "2026-10-04"]
    """

    return get_asofdates(connection)


@router.get("/asofdates/{asofdate}/versions", response_model=list[datetime])
def list_versions(
    asofdate: date,
    connection: DatabaseConnection,
) -> list[datetime]:
    """Liste les versions disponibles pour la date reçue dans l'URL.

    Exemple :
        GET /api/asofdates/2026-10-05/versions
        -> ["2026-10-06T11:45:00", "2026-10-06T09:30:00"]

    FastAPI valide automatiquement le format YYYY-MM-DD. Une valeur comme
    ``05-10-2026`` produit donc une réponse HTTP 422.
    """

    return get_versions(connection, asofdate)
