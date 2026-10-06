"""Configuration du backend lue depuis les variables d'environnement."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# Tous les champs techniques du trade fictif vivent ici. Le frontend ne les
# envoie jamais et ne peut donc pas les modifier.
ADJUSTMENT_DEFAULTS = {
    "cdr": 74000,
    "target_instrument_type": "ADJUSTMENT",
    "product_line": "ADJUSTMENT",
    "business_line": "GMD",
    "fosystem": "MANUAL_ADJUSTMENT",
    "leg_type": "0",
    "reporting_entity_code": "14000",
    "cpy_exposure_class": "ADJUSTMENT",
    "issuer_exposure_class": "ADJUSTMENT",
    "able_conso_perimetre": "P1",
}


class Settings(BaseSettings):
    """Valeurs configurables sans les inscrire dans le code source.

    Exemple : DATABASE_URL est lue depuis backend/.env pendant le développement.
    Elle reste optionnelle au démarrage afin que l'API de santé puisse répondre,
    mais les routes qui interrogent PostgreSQL exigent sa présence.
    """

    app_name: str = "LCR Adjustment API"
    api_prefix: str = "/api"
    database_url: str | None = None
    frontend_origin: str = "http://localhost:4200"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Charge la configuration une seule fois pendant la vie du serveur."""

    return Settings()
