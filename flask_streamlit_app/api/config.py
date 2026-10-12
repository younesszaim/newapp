"""Configuration centralisée de l'API Flask."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

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
    """Variables d'environnement validées une seule fois par Pydantic."""

    database_url: str | None = None
    created_by: str = "local_user"
    database_connect_timeout: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Retourne la configuration mise en cache pour toute la vie du processus."""

    return Settings()
