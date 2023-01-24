import json
import pytest

from ckan.tests import (
    factories,
    helpers,
)
from ckan.logic import NotAuthorized

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "name, private, org_role",
    [
        pytest.param(
            "test_package4",
            True,
            "member",
            marks=pytest.mark.raises(exception=NotAuthorized),
            id="member-cannot-create-package",
        ),
        pytest.param(
            "test-package1", True, "editor", id="editor-can-create-private-package"
        ),
        pytest.param(
            "test-package2",
            False,
            "editor",
            marks=pytest.mark.raises(exception=NotAuthorized),
            id="editor-cannot-create-public-package",
        ),
        pytest.param(
            "test_package3", True, "admin", id="admin-can-create-private-package"
        ),
        pytest.param(
            "test_package3",
            False,
            "admin",
            id="admin-can-create-public-package",
        ),
    ],
)
@pytest.mark.usefixtures(
    "emc_clean_db", "with_plugins", "with_request_context", "emc_create_sasdi_themes"
)
def test_create_package(name, private, org_role):
    user = factories.User()
    owner_organization = factories.Organization()
    helpers.call_action(
        "organization_member_create",
        id=owner_organization["id"],
        username=user["name"],
        role=org_role,
    )
    data_dict = {
        "name": name,
        "private": private,
        "title": name,
        "doi": "",
        "metadata_standard_name": "sans1878",
        "metadata_standard_version": "1.1",
        "notes": f"notes for {name}",
        "responsible_party-0-individual_name": "individual",
        "responsible_party-0-position_name": "position",
        "responsible_party-0-role": "owner",
        "responsible_party_contact_info-0-voice": "+27-101-000-000",
        "responsible_party_contact_info-0-facsimile": "+27-101-000-000",
        "responsible_party_contact_address-0-delivery_point": "delivery point",
        "responsible_party_contact_address-0-address_city": "city",
        "responsible_party_contact_address-0-address_administrative_area": "address_area",
        "responsible_party_contact_address-0-electronic_mail_address": "someone@mail",
        "responsible_party_contact_address-0-postal_code": "postalcode",
        "reference_date-0-reference": "2023-01-13",
        "reference_date-0-date_type": "1",
        "iso_topic_category": "biota",
        "owner_org": owner_organization["id"],
        "dataset_language": "en",
        "metadata_language": "en",
        "dataset_character_set": "utf-8",
        "metadata_character_set": "utf-8",
        "dataset_lineage-0-statement": f"dataset_lineage statement for {name}",
        "distribution_format-0-name": "format",
        "distribution_format-0-version": "1.0",
        "online_resource-0-name": "name",
        "online_resource-0-linkeage": "linkage",
        "online_resource-0-description": "1",
        "online_resource-0-application_profile": "application_profile",
        "contact-0-individual_name": "contact",
        "contact-0-organisational_role": "point_of_contact",
        "contact-0-position_name": "contact",
        "contact_information-0-voice": "+27-101-000-000",
        "contact_information-0-facsimile": "+27-101-000-000",
        "contact_address-0-delivery_point": "delivery point",
        "contact_address-0-city": "city",
        "contact_address-0-administrative_area": "address_area",
        "contact_address-0-electronic_mail_address": "someone@mail",
        "contact_address-0-postal_code": "postalcode",
        "maintainer": "Surname, Name, title.",
        "spatial": json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [10.0, 10.0],
                        [10.31, 10.0],
                        [10.31, 10.44],
                        [10.0, 10.44],
                        [10.0, 10.0],
                    ]
                ],
            }
        ),
        "equivalent_scale": "500",
        "spatial_representation_type": "001",
        "spatial_reference_system": "EPSG:4326",
        "reference_system_additional_info-0-description": "desc",
        "metadata_date_stamp-0-stamp": "2020-01-01",
        "metadata_date_stamp-0-date_type": "1",
    }

    helpers.call_action(
        "package_create",
        context={"ignore_auth": False, "user": user["name"]},
        **data_dict,
    )


@pytest.mark.parametrize(
    "name, private, org_role",
    [
        pytest.param(
            "test_package5",
            True,
            "editor",
            id="editor-can-update-private-package",
        ),
        pytest.param(
            "test_package6",
            False,
            "editor",
            marks=pytest.mark.raises(exception=NotAuthorized),
            id="editor-cannot-update-public-package",
        ),
    ],
)
@pytest.mark.usefixtures(
    "emc_clean_db", "with_plugins", "with_request_context", "emc_create_sasdi_themes"
)
def test_update_package(name, private, org_role):
    owner_organization = factories.Organization()
    org_admin = factories.User()
    helpers.call_action(
        "organization_member_create",
        id=owner_organization["id"],
        username=org_admin["name"],
        role="admin",
    )
    user = factories.User()
    helpers.call_action(
        "organization_member_create",
        id=owner_organization["id"],
        username=user["name"],
        role=org_role,
    )
    data_dict = {
        "name": name,
        "private": private,
        "title": name,
        "doi": "",
        "metadata_standard_name": "sans1878",
        "metadata_standard_version": "1.1",
        "notes": f"notes for {name}",
        "responsible_party-0-individual_name": "individual",
        "responsible_party-0-position_name": "position",
        "responsible_party-0-role": "owner",
        "responsible_party_contact_info-0-voice": "+27-101-000-000",
        "responsible_party_contact_info-0-facsimile": "+27-101-000-000",
        "responsible_party_contact_address-0-delivery_point": "delivery point",
        "responsible_party_contact_address-0-address_city": "city",
        "responsible_party_contact_address-0-address_administrative_area": "address_area",
        "responsible_party_contact_address-0-electronic_mail_address": "someone@mail",
        "responsible_party_contact_address-0-postal_code": "postalcode",
        "reference_date-0-reference": "2023-01-13",
        "reference_date-0-date_type": "1",
        "iso_topic_category": "biota",
        "owner_org": owner_organization["id"],
        "dataset_language": "en",
        "metadata_language": "en",
        "dataset_character_set": "utf-8",
        "metadata_character_set": "utf-8",
        "dataset_lineage-0-statement": f"dataset_lineage statement for {name}",
        "distribution_format-0-name": "format",
        "distribution_format-0-version": "1.0",
        "online_resource-0-name": "name",
        "online_resource-0-linkeage": "linkage",
        "online_resource-0-description": "1",
        "online_resource-0-application_profile": "application_profile",
        "contact-0-individual_name": "contact",
        "contact-0-organisational_role": "point_of_contact",
        "contact-0-position_name": "contact",
        "contact_information-0-voice": "+27-101-000-000",
        "contact_information-0-facsimile": "+27-101-000-000",
        "contact_address-0-delivery_point": "delivery point",
        "contact_address-0-city": "city",
        "contact_address-0-administrative_area": "address_area",
        "contact_address-0-electronic_mail_address": "someone@mail",
        "contact_address-0-postal_code": "postalcode",
        "maintainer": "Surname, Name, title.",
        "spatial": json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [10.0, 10.0],
                        [10.31, 10.0],
                        [10.31, 10.44],
                        [10.0, 10.44],
                        [10.0, 10.0],
                    ]
                ],
            }
        ),
        "equivalent_scale": "500",
        "spatial_representation_type": "001",
        "spatial_reference_system": "EPSG:4326",
        "reference_system_additional_info-0-description": "desc",
        "metadata_date_stamp-0-stamp": "2020-01-01",
        "metadata_date_stamp-0-date_type": "1",
    }
    helpers.call_action(
        "package_create",
        context={"ignore_auth": False, "user": org_admin["name"]},
        **data_dict,
    )
    patched_notes = f"patched notes"
    helpers.call_action(
        "package_patch",
        context={"ignore_auth": False, "user": user["name"]},
        id=name,
        notes=patched_notes,
    )
