"""Unit tests for :class:`DatavicODPDatapusherPlusPlugin` and theme hooks.

Dispatch, re-ingest, and format inference are tested with
``_submit_to_datapusher`` patched. Parent-plugin paths
(``resource_create``, ``IResourceUrlChange``, ``task_status`` idempotency)
are not duplicated here.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ckan.model.domain_object import DomainObjectOperation
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.plugins import toolkit

from ckanext.datavic_odp_theme.datapusher_plus_plugin import (
    DatavicODPDatapusherPlusPlugin,
)
from ckanext.datavic_odp_theme.plugin import DatavicODPTheme

PLUGIN_MODULE = "ckanext.datavic_odp_theme.datapusher_plus_plugin"
THEME_MODULE = "ckanext.datavic_odp_theme.plugin"


@pytest.fixture
def plugin(mocker):
    instance = DatavicODPDatapusherPlusPlugin()
    mocker.patch.object(instance, "_submit_to_datapusher")
    return instance


@pytest.fixture
def theme_plugin():
    return DatavicODPTheme()


@pytest.fixture
def resource_entity():
    entity = MagicMock(spec=Resource)
    entity.id = "res-1"
    return entity


@pytest.fixture
def odp_package_entity():
    entity = MagicMock(spec=Package)
    entity.id = "pkg-1"
    return entity


class TestNotifyDispatch:
    """``notify`` dispatch for ``Resource`` and ``Package`` operations."""

    def test_ignores_non_resource_non_package_entities(self, plugin, mocker):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")
        other = MagicMock()

        plugin.notify(other, DomainObjectOperation.new)

        get_action.assert_not_called()
        plugin._submit_to_datapusher.assert_not_called()

    def test_ignores_changed_resources(self, plugin, resource_entity, mocker):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(resource_entity, DomainObjectOperation.changed)

        get_action.assert_not_called()
        plugin._submit_to_datapusher.assert_not_called()

    def test_ignores_deleted_resources(self, plugin, resource_entity, mocker):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(resource_entity, DomainObjectOperation.deleted)

        get_action.assert_not_called()
        plugin._submit_to_datapusher.assert_not_called()

    def test_new_resource_submits_with_resource_dict(
        self, plugin, resource_entity, mocker
    ):
        """Inline resource via ``notify(Resource, new)``."""
        resource_dict = {
            "id": "res-1",
            "url": "https://example.com/data.csv",
            "format": "CSV",
        }
        resource_show = MagicMock(return_value=resource_dict)
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action", return_value=resource_show
        )

        plugin.notify(resource_entity, DomainObjectOperation.new)

        resource_show.assert_called_once_with(
            {"ignore_auth": True}, {"id": "res-1"}
        )
        plugin._submit_to_datapusher.assert_called_once_with(resource_dict)

    def test_new_resource_swallows_object_not_found(
        self, plugin, resource_entity, mocker
    ):
        resource_show = MagicMock(side_effect=toolkit.ObjectNotFound)
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action", return_value=resource_show
        )

        plugin.notify(resource_entity, DomainObjectOperation.new)

        plugin._submit_to_datapusher.assert_not_called()

    def test_ignores_package_new_operation(self, plugin, odp_package_entity, mocker):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(odp_package_entity, DomainObjectOperation.new)

        get_action.assert_not_called()
        plugin._submit_to_datapusher.assert_not_called()

    def test_ignores_package_deleted_operation(
        self, plugin, odp_package_entity, mocker
    ):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(odp_package_entity, DomainObjectOperation.deleted)

        get_action.assert_not_called()
        plugin._submit_to_datapusher.assert_not_called()


class TestPackageChangedReingest:
    """``Package`` + ``changed`` re-ingest path."""

    def test_package_changed_submits_resources_needing_ingest(
        self, plugin, odp_package_entity, mocker
    ):
        """Resource with empty hash and inactive datastore."""
        pkg_dict = {
            "id": "pkg-1",
            "resources": [
                {
                    "id": "res-1",
                    "url": "https://example.com/data.csv",
                    "format": "CSV",
                    "hash": "",
                    "datastore_active": False,
                }
            ],
        }
        package_show = MagicMock(return_value=pkg_dict)
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action", return_value=package_show
        )

        plugin.notify(odp_package_entity, DomainObjectOperation.changed)

        package_show.assert_called_once_with(
            {"ignore_auth": True}, {"id": "pkg-1"}
        )
        plugin._submit_to_datapusher.assert_called_once_with(
            pkg_dict["resources"][0]
        )

    def test_package_changed_skips_already_ingested_resources(
        self, plugin, odp_package_entity, mocker
    ):
        """Populated hash and active datastore — no submit."""
        pkg_dict = {
            "id": "pkg-1",
            "resources": [
                {
                    "id": "res-1",
                    "hash": "abc123",
                    "datastore_active": True,
                }
            ],
        }
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action",
            return_value=MagicMock(return_value=pkg_dict),
        )

        plugin.notify(odp_package_entity, DomainObjectOperation.changed)

        plugin._submit_to_datapusher.assert_not_called()

    def test_package_changed_submits_only_resources_needing_reingest(
        self, plugin, odp_package_entity, mocker
    ):
        """Mixed resources — only the un-ingested one is submitted."""
        needs_reingest = {
            "id": "res-needs",
            "url": "https://example.com/new.csv",
            "format": "CSV",
            "hash": "",
            "datastore_active": False,
        }
        already_done = {
            "id": "res-done",
            "hash": "populated",
            "datastore_active": True,
        }
        pkg_dict = {
            "id": "pkg-1",
            "resources": [needs_reingest, already_done],
        }
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action",
            return_value=MagicMock(return_value=pkg_dict),
        )

        plugin.notify(odp_package_entity, DomainObjectOperation.changed)

        plugin._submit_to_datapusher.assert_called_once_with(needs_reingest)

    def test_package_changed_swallows_object_not_found(
        self, plugin, odp_package_entity, mocker
    ):
        package_show = MagicMock(side_effect=toolkit.ObjectNotFound)
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action", return_value=package_show
        )

        plugin.notify(odp_package_entity, DomainObjectOperation.changed)

        plugin._submit_to_datapusher.assert_not_called()


class TestShouldReingest:
    def test_true_when_hash_empty_and_datastore_inactive(self, plugin):
        assert plugin._should_reingest({"hash": "", "datastore_active": False})

    def test_true_when_hash_missing_and_datastore_inactive(self, plugin):
        assert plugin._should_reingest({"datastore_active": False}) is True

    def test_false_when_already_ingested(self, plugin):
        assert plugin._should_reingest(
            {"hash": "abc", "datastore_active": True}
        ) is False

    def test_false_when_only_hash_set(self, plugin):
        assert plugin._should_reingest(
            {"hash": "abc", "datastore_active": False}
        ) is False


    def test_false_when_only_datastore_active(self, plugin):
        assert plugin._should_reingest(
            {"hash": "", "datastore_active": True}
        ) is False


class TestInferFormatAndSubmit:
    def test_existing_format_is_preserved(self, plugin):
        resource = {
            "id": "r",
            "url": "https://example.com/data.csv",
            "format": "XLSX",
        }

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "XLSX"
        plugin._submit_to_datapusher.assert_called_once_with(resource)

    def test_format_inferred_from_url_extension(self, plugin):
        resource = {"id": "r", "url": "https://example.com/data.CSV"}

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "csv"
        plugin._submit_to_datapusher.assert_called_once_with(resource)

    def test_format_inference_strips_query_string(self, plugin):
        resource = {
            "id": "r",
            "url": "https://example.com/data.json?token=abc&v=1",
        }

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "json"
        plugin._submit_to_datapusher.assert_called_once_with(resource)

    def test_empty_format_treated_as_missing(self, plugin):
        resource = {
            "id": "r",
            "url": "https://example.com/data.tsv",
            "format": "",
        }

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "tsv"
        plugin._submit_to_datapusher.assert_called_once_with(resource)

    def test_url_type_set_skips_inference(self, plugin):
        resource = {
            "id": "r",
            "url": "https://example.com/dataset/res-1/download/x",
            "url_type": "upload",
        }

        plugin._infer_format_and_submit(resource)

        assert "format" not in resource
        plugin._submit_to_datapusher.assert_called_once_with(resource)

    def test_submit_called_even_without_inferable_format(self, plugin):
        resource = {"id": "r", "url": "https://example.com/data"}

        plugin._infer_format_and_submit(resource)

        plugin._submit_to_datapusher.assert_called_once_with(resource)

    def test_non_ingestible_format_still_calls_submit(self, plugin):
        """Format gate is the parent's job; we still call through."""
        resource = {
            "id": "r",
            "url": "https://example.com/page.html",
            "format": "HTML",
        }

        plugin._infer_format_and_submit(resource)

        plugin._submit_to_datapusher.assert_called_once_with(resource)


class TestCombinedNotifySignals:
    """Resource ``new`` and Package ``changed`` may both fire per commit."""

    def test_both_signals_invoke_submit_for_same_resource(
        self, plugin, resource_entity, odp_package_entity, mocker
    ):
        resource_dict = {
            "id": "res-1",
            "url": "https://example.com/data.csv",
            "format": "CSV",
            "hash": "",
            "datastore_active": False,
        }
        pkg_dict = {"id": "pkg-1", "resources": [resource_dict]}

        def get_action(name):
            action = MagicMock()
            if name == "resource_show":
                action.return_value = resource_dict
            elif name == "package_show":
                action.return_value = pkg_dict
            return action

        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action", side_effect=get_action
        )
        plugin.notify(resource_entity, DomainObjectOperation.new)
        plugin.notify(odp_package_entity, DomainObjectOperation.changed)

        assert plugin._submit_to_datapusher.call_count == 2


class TestNotifyEndToEnd:
    def test_new_syndicated_resource_without_format_is_inferred_and_submitted(
        self, plugin, resource_entity, mocker
    ):
        resource_dict = {
            "id": "res-1",
            "url": "https://syndicate.example.com/dataset/file.geojson?v=2",
        }
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action",
            return_value=MagicMock(return_value=resource_dict),
        )

        plugin.notify(resource_entity, DomainObjectOperation.new)

        plugin._submit_to_datapusher.assert_called_once()
        submitted = plugin._submit_to_datapusher.call_args[0][0]
        assert submitted["id"] == "res-1"
        assert submitted["format"] == "geojson"


class TestDatavicODPThemeGroupAssignment:
    """Category/group logic on ``DatavicODPTheme``."""

    def test_after_dataset_create_assigns_category_group(self, theme_plugin, mocker):
        group = MagicMock()
        mocker.patch(f"{THEME_MODULE}.model.Group.get", return_value=group)
        mocker.patch(
            "builtins.repr", return_value="<Request 'http://localhost/dataset/new'>"
        )
        mocker.patch(
            f"{THEME_MODULE}.tk.get_endpoint",
            return_value=("dataset", "new"),
        )

        theme_plugin.after_dataset_create(
            {},
            {
                "name": "test-dataset",
                "type": "dataset",
                "category": "health",
            },
        )

        group.add_package_by_name.assert_called_once_with("test-dataset")

    def test_after_dataset_create_skips_group_assignment_without_ui_request(
        self, theme_plugin, mocker
    ):
        group = MagicMock()
        mocker.patch(f"{THEME_MODULE}.model.Group.get", return_value=group)
        mocker.patch("builtins.repr", return_value="<LocalProxy unbound>")

        theme_plugin.after_dataset_create(
            {},
            {
                "name": "test-dataset",
                "category": "health",
                "type": "dataset",
            },
        )

        group.add_package_by_name.assert_not_called()

    def test_after_dataset_update_assigns_category_group(self, theme_plugin, mocker):
        group = MagicMock()
        existing_group = MagicMock()
        package = MagicMock()
        package.get_groups.return_value = [existing_group]
        mocker.patch(f"{THEME_MODULE}.model.Group.get", return_value=group)

        theme_plugin.after_dataset_update(
            {"package": package},
            {"name": "test-dataset", "category": "health"},
        )

        group.add_package_by_name.assert_called_once_with("test-dataset")

    def test_after_dataset_update_skips_when_group_already_assigned(
        self, theme_plugin, mocker
    ):
        group = MagicMock()
        package = MagicMock()
        package.get_groups.return_value = [group]
        mocker.patch(f"{THEME_MODULE}.model.Group.get", return_value=group)

        theme_plugin.after_dataset_update(
            {"package": package},
            {"name": "test-dataset", "category": "health"},
        )

        group.add_package_by_name.assert_not_called()
