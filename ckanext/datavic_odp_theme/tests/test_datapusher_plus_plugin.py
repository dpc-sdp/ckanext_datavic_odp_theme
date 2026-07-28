"""Unit tests for :class:`DatavicDatapusherPlusPlugin` and theme hooks.

A standalone ``SingletonPlugin`` (not a ``DatapusherPlusPlugin`` subclass,
to avoid a ``notify()`` collision between ``IResourceUrlChange`` and
``IDomainObjectModification``). ``ckan.plugins.get_plugin`` is patched so no
real ``datapusher_plus`` instance is needed.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ckan.model.domain_object import DomainObjectOperation
from ckan.model.package import Package
from ckan.model.resource import Resource
from ckan.plugins import toolkit

from ckanext.datavic_odp_theme.datapusher_plus_plugin import (
    REQUIRED_PLUGIN,
    DatavicDatapusherPlusPlugin,
)
from ckanext.datavic_odp_theme.plugin import DatavicODPTheme

PLUGIN_MODULE = "ckanext.datavic_odp_theme.datapusher_plus_plugin"
THEME_MODULE = "ckanext.datavic_odp_theme.plugin"


@pytest.fixture
def mock_get_plugin(mocker):
    """Patch get_plugin so no real datapusher_plus instance is needed."""
    mock = mocker.patch(f"{PLUGIN_MODULE}.p.get_plugin")
    mock.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_dpp(mock_get_plugin):
    """The mocked live ``datapusher_plus`` plugin instance."""
    return mock_get_plugin.return_value


@pytest.fixture
def plugin(mock_dpp):
    # Bypass SingletonPlugin's instance-sharing machinery — this class
    # isn't loaded as a real CKAN plugin in the test config.
    return object.__new__(DatavicDatapusherPlusPlugin)


@pytest.fixture
def theme_plugin():
    return DatavicODPTheme()


@pytest.fixture
def resource_entity():
    """A SQLAlchemy ``Resource``-shaped mock that passes ``isinstance``."""
    entity = MagicMock(spec=Resource)
    entity.id = "res-1"
    return entity


@pytest.fixture
def package_entity():
    entity = MagicMock(spec=Package)
    entity.id = "pkg-1"
    return entity


class TestConfigure:
    """Fails fast at load time if datapusher_plus isn't enabled, rather
    than a confusing AttributeError deep inside notify()."""

    def test_raises_when_required_plugin_not_loaded(self, plugin, mocker):
        mocker.patch(f"{PLUGIN_MODULE}.p.plugin_loaded", return_value=False)

        with pytest.raises(Exception, match=REQUIRED_PLUGIN):
            plugin.configure({})

    def test_does_not_raise_when_required_plugin_loaded(self, plugin, mocker):
        mocker.patch(f"{PLUGIN_MODULE}.p.plugin_loaded", return_value=True)

        plugin.configure({})

    def test_checks_the_datapusher_plus_plugin_name(self, plugin, mocker):
        mock_plugin_loaded = mocker.patch(
            f"{PLUGIN_MODULE}.p.plugin_loaded", return_value=True
        )

        plugin.configure({})

        mock_plugin_loaded.assert_called_once_with("datapusher_plus")


class TestSubmitDelegation:
    """Submission goes through the live datapusher_plus instance by name."""

    def test_looks_up_datapusher_plus_by_name(self, plugin, mock_get_plugin):
        resource = {"id": "r", "url": "https://example.com/data.csv", "format": "CSV"}

        plugin._infer_format_and_submit(resource)

        mock_get_plugin.assert_called_once_with("datapusher_plus")

    def test_submits_to_the_looked_up_instance(self, plugin, mock_dpp):
        resource = {"id": "r", "url": "https://example.com/data.csv", "format": "CSV"}

        plugin._infer_format_and_submit(resource)

        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)


class TestNotifyDispatch:
    """Only submits for new Resources and changed Packages; every other
    combination is out of scope (IResourceUrlChange's job) or a no-op."""

    def test_operation_is_required_no_default(self, plugin):
        """Regression guard: a default here would silently mask a future
        mistake reintroducing the IResourceUrlChange collision."""
        with pytest.raises(TypeError):
            plugin.notify(MagicMock())

    def test_ignores_non_resource_non_package_entities(self, plugin, mock_dpp, mocker):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")
        other = MagicMock()

        plugin.notify(other, DomainObjectOperation.new)

        get_action.assert_not_called()
        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_ignores_changed_resources(self, plugin, mock_dpp, resource_entity, mocker):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(resource_entity, DomainObjectOperation.changed)

        get_action.assert_not_called()
        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_ignores_deleted_resources(self, plugin, mock_dpp, resource_entity, mocker):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(resource_entity, DomainObjectOperation.deleted)

        get_action.assert_not_called()
        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_new_resource_submits_with_resource_dict(
        self, plugin, mock_dpp, resource_entity, mocker
    ):
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
        mock_dpp._submit_to_datapusher.assert_called_once_with(resource_dict)

    def test_new_resource_swallows_object_not_found(
        self, plugin, mock_dpp, resource_entity, mocker
    ):
        resource_show = MagicMock(side_effect=toolkit.ObjectNotFound)
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action", return_value=resource_show
        )

        plugin.notify(resource_entity, DomainObjectOperation.new)

        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_ignores_package_new_operation(
        self, plugin, mock_dpp, package_entity, mocker
    ):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(package_entity, DomainObjectOperation.new)

        get_action.assert_not_called()
        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_ignores_package_deleted_operation(
        self, plugin, mock_dpp, package_entity, mocker
    ):
        get_action = mocker.patch(f"{PLUGIN_MODULE}.toolkit.get_action")

        plugin.notify(package_entity, DomainObjectOperation.deleted)

        get_action.assert_not_called()
        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_package_changed_submits_resources_needing_ingest(
        self, plugin, mock_dpp, package_entity, mocker
    ):
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

        plugin.notify(package_entity, DomainObjectOperation.changed)

        package_show.assert_called_once_with(
            {"ignore_auth": True}, {"id": "pkg-1"}
        )
        mock_dpp._submit_to_datapusher.assert_called_once_with(
            pkg_dict["resources"][0]
        )

    def test_package_changed_skips_already_ingested_resources(
        self, plugin, mock_dpp, package_entity, mocker
    ):
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

        plugin.notify(package_entity, DomainObjectOperation.changed)

        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_package_changed_submits_only_resources_needing_reingest(
        self, plugin, mock_dpp, package_entity, mocker
    ):
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

        plugin.notify(package_entity, DomainObjectOperation.changed)

        mock_dpp._submit_to_datapusher.assert_called_once_with(needs_reingest)

    def test_package_changed_swallows_object_not_found(
        self, plugin, mock_dpp, package_entity, mocker
    ):
        package_show = MagicMock(side_effect=toolkit.ObjectNotFound)
        mocker.patch(
            f"{PLUGIN_MODULE}.toolkit.get_action", return_value=package_show
        )

        plugin.notify(package_entity, DomainObjectOperation.changed)

        mock_dpp._submit_to_datapusher.assert_not_called()

    def test_combined_resource_new_and_package_changed_signals(
        self, plugin, mock_dpp, resource_entity, package_entity, mocker
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
        plugin.notify(package_entity, DomainObjectOperation.changed)

        assert mock_dpp._submit_to_datapusher.call_count == 2


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
    """Always submits — only the format varies. datapusher_plus silently
    no-ops on a missing format, so this fills one in first."""

    def test_existing_format_is_preserved(self, plugin, mock_dpp):
        resource = {
            "id": "r",
            "url": "https://example.com/data.csv",
            "format": "XLSX",
        }

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "XLSX"
        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)

    def test_format_inferred_from_url_extension(self, plugin, mock_dpp):
        resource = {"id": "r", "url": "https://example.com/data.CSV"}

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "csv"
        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)

    def test_format_inference_strips_query_string(self, plugin, mock_dpp):
        resource = {
            "id": "r",
            "url": "https://example.com/data.json?token=abc&v=1",
        }

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "json"
        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)

    def test_empty_format_treated_as_missing(self, plugin, mock_dpp):
        resource = {
            "id": "r",
            "url": "https://example.com/data.tsv",
            "format": "",
        }

        plugin._infer_format_and_submit(resource)

        assert resource["format"] == "tsv"
        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)

    def test_url_type_set_skips_inference(self, plugin, mock_dpp):
        resource = {
            "id": "r",
            "url": "https://example.com/dataset/res-1/download/x",
            "url_type": "upload",
        }

        plugin._infer_format_and_submit(resource)

        assert "format" not in resource
        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)

    def test_submit_called_even_without_inferable_format(self, plugin, mock_dpp):
        resource = {"id": "r", "url": "https://example.com/data"}

        plugin._infer_format_and_submit(resource)

        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)

    def test_non_ingestible_format_still_calls_submit(self, plugin, mock_dpp):
        """Format support is datapusher_plus's own gate to enforce."""
        resource = {
            "id": "r",
            "url": "https://example.com/page.html",
            "format": "HTML",
        }

        plugin._infer_format_and_submit(resource)

        mock_dpp._submit_to_datapusher.assert_called_once_with(resource)


class TestNotifyEndToEnd:
    def test_new_syndicated_resource_without_format_is_inferred_and_submitted(
        self, plugin, mock_dpp, resource_entity, mocker
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

        mock_dpp._submit_to_datapusher.assert_called_once()
        submitted = mock_dpp._submit_to_datapusher.call_args[0][0]
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
