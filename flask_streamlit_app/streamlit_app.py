"""Point d'entrée de l'interface Streamlit."""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FLASK_API_URL", "http://127.0.0.1:5000")


@st.cache_data(ttl=30)
def load_asofdates() -> list[str]:
    """Charge les dates depuis Flask et les garde 30 secondes en cache."""

    response = requests.get(f"{API_URL}/api/asofdates", timeout=10)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=30)
def load_versions(asofdate: str) -> list[str]:
    """Charge uniquement les versions de la date sélectionnée."""

    response = requests.get(
        f"{API_URL}/api/asofdates/{asofdate}/versions",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=30)
def load_lcr_summary(asofdate: str, version: str) -> dict:
    """Charge les agrégats LCR du contexte complet."""

    response = requests.get(
        f"{API_URL}/api/lcr-summary",
        params={"asofdate": asofdate, "version": version},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def format_euro(value: float) -> str:
    """Affiche un montant compact dans les cartes KPI."""

    absolute_value = abs(value)
    if absolute_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} Bn€"
    if absolute_value >= 1_000_000:
        return f"{value / 1_000_000:.2f} M€"
    if absolute_value >= 1_000:
        return f"{value / 1_000:.2f} K€"
    return f"{value:.2f} €"

st.set_page_config(page_title="LCR Adjustments", page_icon="🏦", layout="wide")

st.title("LCR Adjustments")
st.caption("Prototype Flask + Streamlit — thème CACIB à venir")

st.subheader("État de l'API")

try:
    response = requests.get(f"{API_URL}/api/health", timeout=3)
    response.raise_for_status()
    st.success("API Flask connectée")
except requests.RequestException:
    st.warning("API Flask indisponible. Démarrez-la avec la commande du README.")

st.divider()
st.subheader("Contexte LCR")

try:
    asofdates = load_asofdates()
    selected_asofdate = st.selectbox(
        "Date d'arrêté",
        options=asofdates,
        index=None,
        placeholder="Sélectionnez une date",
    )
    if selected_asofdate:
        versions = load_versions(selected_asofdate)
        selected_version = st.selectbox(
            "Version",
            options=versions,
            index=None,
            placeholder="Sélectionnez une version",
        )
        if selected_version:
            summary = load_lcr_summary(selected_asofdate, selected_version)
            st.subheader("Résumé LCR")
            total = summary["total"]
            columns = st.columns(4)
            columns[0].metric("Montant 0D", format_euro(total["amount0d"]))
            columns[1].metric("Montant 30D", format_euro(total["amount30d"]))
            columns[2].metric("LCR réglementaire", format_euro(total["lcrReglementaire"]))
            columns[3].metric("LCR gestion", format_euro(total["lcrGestion"]))

            st.dataframe(
                summary["rows"],
                column_order=(
                    "productLine", "amount0d", "amount30d",
                    "lcrReglementaire", "lcrGestion",
                ),
                column_config={
                    "productLine": "Product Line",
                    "amount0d": st.column_config.NumberColumn("Montant 0D", format="%.2f €"),
                    "amount30d": st.column_config.NumberColumn("Montant 30D", format="%.2f €"),
                    "lcrReglementaire": st.column_config.NumberColumn("LCR réglementaire", format="%.2f €"),
                    "lcrGestion": st.column_config.NumberColumn("LCR gestion", format="%.2f €"),
                },
                hide_index=True,
                use_container_width=True,
            )
except requests.RequestException:
    st.error("Impossible de charger le contexte LCR depuis PostgreSQL.")
