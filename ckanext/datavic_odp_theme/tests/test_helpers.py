import pytest
from faker import Faker

import ckan.plugins.toolkit as tk

from ckanext.datavic_odp_theme.const import NOT_DOWNLOADABLE_FORMATS


fake = Faker()


@pytest.fixture
def resource_data():
    def func(**kwargs):
        data_dict = {
            "id": fake.uuid4(),
            "url": fake.url(),
            "name": fake.slug(fake.sentence(nb_words=5)),
            "format": "csv",
        }
        data_dict.update(kwargs)
        return data_dict

    return func


class TestHelpers:
    @pytest.mark.usefixtures("clean_db")
    def test_resource_formats_list(self, dataset_factory, resource_data):
        dataset_factory(
            resources=[
                resource_data(),
                resource_data(),
                resource_data(format="xml"),
                resource_data(format=""),
            ]
        )

        format_list: list[str] = tk.h.format_list()
        assert format_list == ["CSV", "XML"]

    @pytest.mark.usefixtures("clean_db")
    def test_resource_formats_list_no_resources(self):
        assert not tk.h.format_list()

    def test_is_resource_downloadable(self, resource_data):
        assert tk.h.is_resource_downloadable(resource_data())
        assert tk.h.is_resource_downloadable(
            resource_data(format="api", has_views=True)
        )
        assert tk.h.is_resource_downloadable(
            resource_data(format="api", url_type="upload")
        )

        for res_format in NOT_DOWNLOADABLE_FORMATS:
            assert not tk.h.is_resource_downloadable(resource_data(format=res_format))

    def test_organization_list_no_orgs(self):
        assert not tk.h.organization_list()

    @pytest.mark.usefixtures("clean_db")
    def test_organization_list_with_org(self, organization):
        org_list = tk.h.organization_list()

        assert org_list
        assert isinstance(org_list, list)
        assert isinstance(org_list[0], dict)
        assert len(org_list) == 1

    def test_organization_list_no_groups(self):
        assert not tk.h.group_list()

    @pytest.mark.usefixtures("clean_db")
    def test_organization_list_no_groups_org(self, organization):
        assert not tk.h.group_list()

    @pytest.mark.usefixtures("clean_db")
    def test_organization_list_with_group(self, group):
        group_list = tk.h.group_list()

        assert group_list
        assert isinstance(group_list, list)
        assert isinstance(group_list[0], dict)
        assert len(group_list) == 1
