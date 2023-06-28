import pytest

from ckan.lib import jobs
from ckan.tests.helpers import call_action


@pytest.mark.usefixtures("with_test_worker", "clean_db")
class TestOrganizationReindex:
    """Updating the organization must reindex the dataset to update
    the organization metadata linked to the dataset"""
    def test_organization_reindex(self, organization, sysadmin, dataset_factory):
        dataset = dataset_factory(owner_org=organization["id"])
        organization["title"] = "new org title"

        result = call_action(
            "organization_update",
            **organization,
            context={"user": sysadmin["name"]}
        )

        jobs.Worker().work(True)

        result = call_action("package_show", id=dataset["id"])
        assert result["organization"]["title"] == organization["title"]
