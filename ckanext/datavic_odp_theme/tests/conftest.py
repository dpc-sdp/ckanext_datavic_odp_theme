import factory
from faker import Faker
from pytest_factoryboy import register

import ckan.tests.factories as factories

faker = Faker()


class DatasetFactory(factories.Dataset):
    date_created_data_asset = factory.LazyAttribute(lambda _: faker.date())
    license_id = "other-open"


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
