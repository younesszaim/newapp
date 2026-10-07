"""Point d'entrée de l'interface Streamlit."""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FLASK_API_URL", "http://127.0.0.1:5000")

st.set_page_config(page_title="LCR Adjustments", page_icon="🏦", layout="wide")

st.title("LCR Adjustments")
st.caption("Prototype Flask + Streamlit — thème CACIB à venir")

st.subheader("État de l'API")

try:
    response = requests.get(f"{API_URL}/api/health", timeout=3)
    response.raise_for_status()
    st.success("API Flask connectée")
    st.json(response.json())
except requests.RequestException:
    st.warning("API Flask indisponible. Démarrez-la avec la commande du README.")
