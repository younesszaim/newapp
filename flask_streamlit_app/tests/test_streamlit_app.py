"""Exemples des fonctions Streamlit sans ouvrir de navigateur."""

from contextlib import nullcontext
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd

import streamlit_app as ui


class StreamlitAppTest(TestCase):
    def tearDown(self) -> None:
        ui.load_asofdates.clear()
        ui.load_versions.clear()
        ui.load_lcr_summary.clear()
        ui.load_registry.clear()

    @patch("streamlit_app.requests.get")
    def test_api_get_builds_url_and_returns_json(self, get: MagicMock) -> None:
        get.return_value.json.return_value = ["example"]

        result = ui.api_get("/api/example", params={"page": 1})

        self.assertEqual(result, ["example"])
        get.assert_called_once_with(
            f"{ui.API_URL}/api/example", timeout=30, params={"page": 1}
        )
        get.return_value.raise_for_status.assert_called_once()

    @patch("streamlit_app.api_get")
    def test_cached_loaders_call_expected_endpoints(self, api_get: MagicMock) -> None:
        api_get.return_value = []

        ui.load_asofdates()
        ui.load_versions("2026-10-05")
        ui.load_lcr_summary("2026-10-05", "2026-10-06T15:30:00")
        ui.load_registry()

        self.assertEqual(api_get.call_args_list[0].args[0], "/api/asofdates")
        self.assertIn("/versions", api_get.call_args_list[1].args[0])
        self.assertEqual(api_get.call_args_list[2].args[0], "/api/lcr-summary")
        self.assertEqual(api_get.call_args_list[3].args[0], "/api/adjustments")

    def test_format_euro_uses_readable_units(self) -> None:
        examples = {
            12: "12.00 €",
            12_000: "12.00 K€",
            12_000_000: "12.00 M€",
            12_000_000_000: "12.00 Bn€",
        }
        for value, expected in examples.items():
            with self.subTest(value=value):
                self.assertEqual(ui.format_euro(value), expected)

    @patch("streamlit_app.requests.post")
    def test_save_adjustments_posts_one_batch(self, post: MagicMock) -> None:
        post.return_value.json.return_value = {"adjustmentId": "id-1"}
        rows = [{"ldpImpactLcrReglementaire": 100}]

        result = ui.save_adjustments("2026-10-05", "version-1", rows)

        self.assertEqual(result, {"adjustmentId": "id-1"})
        self.assertEqual(post.call_args.kwargs["json"]["adjustments"], rows)

    @patch("streamlit_app.requests.delete")
    def test_delete_adjustment_calls_block_endpoint(self, delete: MagicMock) -> None:
        ui.delete_adjustment("adjustment-1")

        self.assertTrue(delete.call_args.args[0].endswith("/adjustments/adjustment-1"))
        delete.return_value.raise_for_status.assert_called_once()

    @patch("streamlit_app.st")
    @patch("streamlit_app.load_lcr_summary")
    def test_show_summary_displays_four_metrics(
        self, load_summary: MagicMock, st: MagicMock
    ) -> None:
        load_summary.return_value = {
            "total": {
                "amount0d": 1, "amount30d": 2,
                "lcrReglementaire": 3, "lcrGestion": 4,
            },
            "rows": [],
        }
        st.columns.return_value = [MagicMock() for _ in range(4)]

        ui.show_summary("2026-10-05", "version-1")

        self.assertEqual(sum(column.metric.call_count for column in st.columns.return_value), 4)
        st.dataframe.assert_called_once()

    @patch("streamlit_app.st")
    def test_editor_can_render_without_submitting(self, st: MagicMock) -> None:
        st.form.return_value = nullcontext()
        st.data_editor.return_value = pd.DataFrame()
        st.form_submit_button.return_value = False

        ui.show_adjustment_editor("2026-10-05", "version-1")

        st.data_editor.assert_called_once()

    @patch("streamlit_app.show_adjustment_editor")
    @patch("streamlit_app.show_summary")
    @patch("streamlit_app.load_versions", return_value=["version-1"])
    @patch("streamlit_app.load_asofdates", return_value=["2026-10-05"])
    @patch("streamlit_app.st")
    def test_create_page_loads_summary_after_context_selection(
        self, st: MagicMock, _dates: MagicMock, _versions: MagicMock,
        show_summary: MagicMock, show_editor: MagicMock,
    ) -> None:
        st.selectbox.side_effect = ["2026-10-05", "version-1"]

        ui.show_create_page()

        show_summary.assert_called_once_with("2026-10-05", "version-1")
        show_editor.assert_called_once_with("2026-10-05", "version-1")

    @patch("streamlit_app._show_active_registry_block")
    @patch("streamlit_app.load_registry")
    @patch("streamlit_app.st")
    def test_registry_separates_active_and_deleted_blocks(
        self, st: MagicMock, load_registry: MagicMock, show_active: MagicMock
    ) -> None:
        load_registry.return_value = [
            self._block("ACTIVE", "2026-10-08T09:00:00"),
            self._block("DELETED", "2026-10-08T10:00:00"),
        ]
        filter_columns = [MagicMock(), MagicMock()]
        filter_columns[0].selectbox.return_value = "Toutes"
        filter_columns[1].selectbox.return_value = "Toutes"
        metric_columns = [MagicMock(), MagicMock(), MagicMock()]
        st.columns.side_effect = [filter_columns, metric_columns]
        st.tabs.return_value = [nullcontext(), nullcontext()]

        ui.show_registry_page()

        show_active.assert_called_once()
        st.dataframe.assert_called_once()

    @patch("streamlit_app.st")
    def test_active_block_is_collapsed_without_delete_click(self, st: MagicMock) -> None:
        st.expander.return_value = nullcontext()
        st.button.return_value = False

        ui._show_active_registry_block(self._block("ACTIVE", "2026-10-08T09:00:00"))

        st.dataframe.assert_called_once()
        st.button.assert_called_once()

    @patch("streamlit_app.show_create_page")
    @patch("streamlit_app.requests.get")
    @patch("streamlit_app.st")
    def test_main_opens_selected_page(
        self, st: MagicMock, get: MagicMock, show_create: MagicMock
    ) -> None:
        st.sidebar.radio.return_value = "Créer un ajustement"

        ui.main()

        get.return_value.raise_for_status.assert_called_once()
        show_create.assert_called_once()

    @staticmethod
    def _block(status: str, last_event: str) -> dict:
        return {
            "adjustmentId": f"id-{status}",
            "asofdate": "2026-10-05",
            "asofdateflowVersion": "2026-10-06T15:30:00",
            "createdAt": "2026-10-08T09:00:00",
            "createdBy": "local_user",
            "status": status,
            "deletedAt": last_event if status == "DELETED" else None,
            "deletedBy": "local_user" if status == "DELETED" else None,
            "lastEventAt": last_event,
            "lines": [] if status == "DELETED" else [{"tradeNo": 123}],
        }
