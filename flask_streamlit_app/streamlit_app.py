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
            st.success(
                f"Contexte sélectionné : {selected_asofdate} · {selected_version}"
            )
except requests.RequestException:
    st.error("Impossible de charger le contexte LCR depuis PostgreSQL.")
