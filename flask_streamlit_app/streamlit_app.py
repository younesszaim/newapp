"""Interface Streamlit de gestion des ajustements LCR."""

import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("FLASK_API_URL", "http://127.0.0.1:5000")


def api_get(path: str, **kwargs) -> dict | list:
    response = requests.get(f"{API_URL}{path}", timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=30)
def load_asofdates() -> list[str]:
    return api_get("/api/asofdates")


@st.cache_data(ttl=30)
def load_versions(asofdate: str) -> list[str]:
    return api_get(f"/api/asofdates/{asofdate}/versions")


@st.cache_data(ttl=30)
def load_lcr_summary(asofdate: str, version: str) -> dict:
    return api_get(
        "/api/lcr-summary",
        params={"asofdate": asofdate, "version": version},
    )


@st.cache_data(ttl=15)
def load_registry() -> list[dict]:
    return api_get("/api/adjustments")


def format_euro(value: float) -> str:
    absolute_value = abs(value)
    for threshold, divisor, suffix in (
        (1_000_000_000, 1_000_000_000, "Bn€"),
        (1_000_000, 1_000_000, "M€"),
        (1_000, 1_000, "K€"),
    ):
        if absolute_value >= threshold:
            return f"{value / divisor:.2f} {suffix}"
    return f"{value:.2f} €"


def save_adjustments(asofdate: str, version: str, rows: list[dict]) -> dict:
    response = requests.post(
        f"{API_URL}/api/adjustments",
        json={
            "asofdate": asofdate,
            "asofdateflowVersion": version,
            "adjustments": rows,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def delete_adjustment(adjustment_id: str) -> None:
    response = requests.delete(
        f"{API_URL}/api/adjustments/{adjustment_id}", timeout=30
    )
    response.raise_for_status()


def show_summary(asofdate: str, version: str) -> None:
    summary = load_lcr_summary(asofdate, version)
    st.subheader("Résumé LCR")
    total = summary["total"]
    columns = st.columns(4)
    columns[0].metric("Montant 0D", format_euro(total["amount0d"]))
    columns[1].metric("Montant 30D", format_euro(total["amount30d"]))
    columns[2].metric("LCR réglementaire", format_euro(total["lcrReglementaire"]))
    columns[3].metric("LCR gestion", format_euro(total["lcrGestion"]))
    st.dataframe(summary["rows"], hide_index=True, use_container_width=True)


def show_adjustment_editor(asofdate: str, version: str) -> None:
    st.subheader("Nouvel ajustement")
    st.caption("* Colonnes obligatoires · les cellules optionnelles vides valent 0 €")
    initial_rows = pd.DataFrame([{
        "ldpImpactLcrReglementaire": None,
        "ldpImpactLcrGestion": None,
        "impactLcrInflow": 0.0,
        "impactLcrOutflow": 0.0,
        "impactLcrAsset": 0.0,
        "impactLcrAssetCash": 0.0,
    }])
    with st.form("adjustment_form"):
        edited_rows = st.data_editor(
            initial_rows,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            column_config={
                "ldpImpactLcrReglementaire": st.column_config.NumberColumn("LCR réglementaire *", required=True, format="%.2f €"),
                "ldpImpactLcrGestion": st.column_config.NumberColumn("LCR gestion *", required=True, format="%.2f €"),
                "impactLcrInflow": st.column_config.NumberColumn("Inflow · Optionnel", format="%.2f €"),
                "impactLcrOutflow": st.column_config.NumberColumn("Outflow · Optionnel", format="%.2f €"),
                "impactLcrAsset": st.column_config.NumberColumn("Asset · Optionnel", format="%.2f €"),
                "impactLcrAssetCash": st.column_config.NumberColumn("Asset Cash · Optionnel", format="%.2f €"),
            },
        )
        confirmed = st.checkbox("Je confirme l'enregistrement de toutes ces lignes")
        submitted = st.form_submit_button("Enregistrer l'ajustement", type="primary")

    if not submitted:
        return
    if not confirmed:
        st.error("Confirmez l'enregistrement avant de continuer.")
        return
    if len(edited_rows) > 100:
        st.error("Un ajustement ne peut pas dépasser 100 lignes.")
        return
    try:
        rows = edited_rows.where(pd.notna(edited_rows), None).to_dict("records")
        result = save_adjustments(asofdate, version, rows)
        load_lcr_summary.clear()
        load_registry.clear()
        st.success(
            f"Ajustement {result['adjustmentId']} enregistré avec "
            f"{result['lineCount']} ligne(s)."
        )
    except requests.HTTPError as error:
        st.error(error.response.json().get("error", "Requête invalide."))


def show_create_page() -> None:
    st.header("Créer un ajustement")
    asofdate = st.selectbox(
        "Date d'arrêté", load_asofdates(), index=None,
        placeholder="Sélectionnez une date",
    )
    if not asofdate:
        return
    version = st.selectbox(
        "Version", load_versions(asofdate), index=None,
        placeholder="Sélectionnez une version",
    )
    if version:
        show_summary(asofdate, version)
        show_adjustment_editor(asofdate, version)


def show_registry_page() -> None:
    st.header("Registre des ajustements")
    blocks = load_registry()
    if not blocks:
        st.info("Aucun ajustement enregistré.")
        return

    dates = sorted({block["asofdate"] for block in blocks}, reverse=True)
    filter_columns = st.columns(2)
    selected_date = filter_columns[0].selectbox(
        "Date d'arrêté", ["Toutes", *dates]
    )
    versions = sorted(
        {
            block["asofdateflowVersion"]
            for block in blocks
            if selected_date == "Toutes" or block["asofdate"] == selected_date
        },
        reverse=True,
    )
    selected_version = filter_columns[1].selectbox(
        "Version", ["Toutes", *versions]
    )
    filtered = sorted(
        [
            block for block in blocks
            if (selected_date == "Toutes" or block["asofdate"] == selected_date)
            and (
                selected_version == "Toutes"
                or block["asofdateflowVersion"] == selected_version
            )
        ],
        key=lambda block: block["lastEventAt"],
        reverse=True,
    )
    active_blocks = [block for block in filtered if block["status"] == "ACTIVE"]
    deleted_blocks = [block for block in filtered if block["status"] == "DELETED"]

    metrics = st.columns(3)
    metrics[0].metric("Ajustements actifs", len(active_blocks))
    metrics[1].metric(
        "Lignes actives", sum(len(block["lines"]) for block in active_blocks)
    )
    metrics[2].metric("Ajustements supprimés", len(deleted_blocks))

    active_tab, deleted_tab = st.tabs(
        (f"Actifs ({len(active_blocks)})", f"Supprimés ({len(deleted_blocks)})")
    )
    with active_tab:
        if not active_blocks:
            st.info("Aucun ajustement actif pour ces filtres.")
        for block in active_blocks:
            _show_active_registry_block(block)

    with deleted_tab:
        if not deleted_blocks:
            st.info("Aucun ajustement supprimé pour ces filtres.")
        else:
            st.dataframe(
                [
                    {
                        "Dernier événement": block["lastEventAt"],
                        "Date d'arrêté": block["asofdate"],
                        "Version": block["asofdateflowVersion"],
                        "Adjustment ID": block["adjustmentId"],
                        "Supprimé par": block["deletedBy"],
                    }
                    for block in deleted_blocks
                ],
                hide_index=True,
                use_container_width=True,
            )


def _show_active_registry_block(block: dict) -> None:
    """Affiche un bloc actif replié, avec son action de suppression."""

    title = (
        f"{block['asofdate']} · {block['asofdateflowVersion']} · "
        f"{len(block['lines'])} ligne(s) · {block['lastEventAt']}"
    )
    with st.expander(title):
        st.code(block["adjustmentId"], language=None)
        st.caption(f"Créé le {block['createdAt']} par {block['createdBy']}")
        st.dataframe(block["lines"], hide_index=True, use_container_width=True)
        confirmed = st.checkbox(
            "Confirmer la suppression de toutes les lignes",
            key=f"confirm-{block['adjustmentId']}",
        )
        if not st.button(
            "Supprimer l'ajustement",
            key=f"delete-{block['adjustmentId']}",
            type="secondary",
        ):
            return
        if not confirmed:
            st.error("Cochez la confirmation avant la suppression.")
            return
        try:
            delete_adjustment(block["adjustmentId"])
            load_registry.clear()
            load_lcr_summary.clear()
            st.success("Toutes les lignes de l'ajustement ont été supprimées.")
            st.rerun()
        except requests.HTTPError as error:
            st.error(error.response.json().get("error", "Suppression impossible."))


st.set_page_config(page_title="LCR Adjustments", page_icon="🏦", layout="wide")
st.title("LCR Adjustments")
st.caption("Application Flask + Streamlit")

page = st.sidebar.radio("Menu", ("Créer un ajustement", "Registre"))
try:
    health = requests.get(f"{API_URL}/api/health", timeout=3)
    health.raise_for_status()
    st.sidebar.success("API Flask connectée")
    show_create_page() if page == "Créer un ajustement" else show_registry_page()
except requests.RequestException:
    st.error("API Flask indisponible. Démarrez-la avec `python -m api.app`.")
