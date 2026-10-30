import factory
import pytest
from faker import Faker
from pytest_factoryboy import register

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

faker = Faker()

_CATEGORY_ID = "9ca71dfb-b758-4901-97ba-08cebe923158"


def _ensure_category_group() -> str:
    """Create the DV category group if it doesn't exist, then return its id.

    The ``category`` field only accepts groups from ``category_list``.
    """
    try:
        tk.get_action("group_show")({"ignore_auth": True}, {"id": _CATEGORY_ID})
    except tk.ObjectNotFound:
        site_user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
        tk.get_action("group_create")(
            {"ignore_auth": True, "user": site_user["name"]},
            {"id": _CATEGORY_ID, "name": "data-themes", "title": "Data Themes"},
        )
    return _CATEGORY_ID


@pytest.fixture(autouse=True)
def load_standard_plugins(with_plugins):
    """Load the plugins in test.ini for every test.

    CKAN's pytest plugin unloads non-system plugins before the run.
    """


class DatasetFactory(factories.Dataset):
    date_created_data_asset = factory.LazyAttribute(lambda _: faker.date())
    license_id = "other-open"
    category = factory.LazyAttribute(lambda _: _ensure_category_group())
    extract = "Test extract."
    personal_information = "no"
    update_frequency = "monthly"
    data_owner = "Data Custodian Team"
    contact_point = "contact@example.vic.gov.au"


register(DatasetFactory, "dataset")


class GroupFactory(factories.Group):
    pass


register(GroupFactory, "group")


class OrganizationFactory(factories.Organization):
    pass


register(OrganizationFactory, "organization")


class SysadminFactory(factories.Sysadmin):
    pass


register(SysadminFactory, "sysadmin")
