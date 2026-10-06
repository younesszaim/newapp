"""Configuration du backend lue depuis les variables d'environnement."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
