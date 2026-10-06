"""Routes permettant de choisir le contexte de reporting LCR."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from psycopg2.extensions import connection as PostgreSQLConnection

from app.database import get_connection
from app.repositories.lcr_repository import get_asofdates

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
