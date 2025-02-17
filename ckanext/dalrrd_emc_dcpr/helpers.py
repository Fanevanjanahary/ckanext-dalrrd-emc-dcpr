import json
import logging
import typing
from urllib.parse import quote
from html import escape as html_escape

from shapely import geometry
from ckan import model
from ckan.plugins import toolkit
from ckan.lib.helpers import build_nav_main as core_build_nav_main

from . import constants
from .logic.action.emc import show_version
from .constants import DCPRRequestStatus
from .model.dcpr_request import DCPRRequest


logger = logging.getLogger(__name__)


def get_sasdi_themes(*args, **kwargs) -> typing.List[typing.Dict[str, str]]:
    logger.debug(f"inside get_sasdi_themes {args=} {kwargs=}")
    try:
        sasdi_themes = toolkit.get_action("tag_list")(
            data_dict={"vocabulary_id": constants.SASDI_THEMES_VOCABULARY_NAME}
        )
    except toolkit.ObjectNotFound:
        sasdi_themes = []
    return [{"value": t, "label": t} for t in sasdi_themes]


def get_iso_topic_categories(*args, **kwargs) -> typing.List[typing.Dict[str, str]]:
    logger.debug(f"inside get_iso_topic_categories {args=} {kwargs=}")
    return [
        {"value": cat[0], "label": cat[1]} for cat in constants.ISO_TOPIC_CATEGORIES
    ]


def get_default_spatial_search_extent(
    padding_degrees: typing.Optional[float] = None,
) -> typing.Dict:
    """
    Return GeoJSON polygon with bbox to use for default view of spatial search map widget.
    """
    configured_extent = toolkit.config.get(
        "ckan.dalrrd_emc_dcpr.default_spatial_search_extent"
    )
    if padding_degrees and configured_extent:
        parsed_extent = json.loads(configured_extent)
        result = _pad_geospatial_extent(parsed_extent, padding_degrees)
    else:
        result = configured_extent
    return result


def get_default_bounding_box() -> typing.Optional[typing.List[float]]:
    """Return the default bounding box in the form upper left, lower right

    This function calculates the default bounding box from the
    `ckan.dalrrd_emc_dcpr.default_spatial_search_extent` configuration value. Note that
    this configuration value is expected to be in GeoJSON format and in GeoJSON,
    coordinate pairs take the form `lon, lat`.

    This function outputs a list with upper left latitude, upper left latitude, lower
    right latitude, lower right longitude.

    """

    configured_extent = toolkit.config.get(
        "ckan.dalrrd_emc_dcpr.default_spatial_search_extent"
    )
    parsed_extent = json.loads(configured_extent)
    return convert_geojson_to_bbox(parsed_extent)


def convert_geojson_to_bbox(
    geojson: typing.Dict,
) -> typing.Optional[typing.List[float]]:
    try:
        coords = geojson["coordinates"][0]
    except TypeError:
        result = None
    else:
        min_lon = min(c[0] for c in coords)
        max_lon = max(c[0] for c in coords)
        min_lat = min(c[1] for c in coords)
        max_lat = max(c[1] for c in coords)
        result = [max_lat, min_lon, min_lat, max_lon]
    return result


def convert_string_extent_to_bbox(extent: str) -> typing.List[float]:
    if extent is None:
        return []
    coords_extent = []
    for value in extent.split(","):
        try:
            coords_extent.append(float(value))
        except ValueError:
            continue
    return coords_extent


def helper_show_version(*args, **kwargs) -> typing.Dict:
    return show_version()


def user_is_org_member(
    org_id: str, user=None, role: typing.Optional[str] = None
) -> bool:
    """Check if user has editor role in the input organization."""
    result = False
    if user is not None:
        member_list_action = toolkit.get_action("member_list")
        try:
            org_members = member_list_action(
                data_dict={"id": org_id, "object_type": "user"}
            )
        except:
            return result
        logger.debug(f"{user.id=}")
        logger.debug(f"{org_members=}")
        for member_id, _, member_role in org_members:
            if user.id == member_id:
                if role is None or member_role.lower() == role.lower():
                    result = True
                break
    return result


def org_member_list(org_id: str, role: typing.Optional[str] = None) -> typing.List:
    """Return list of organization members with the specified role"""
    member_list_action = toolkit.get_action("member_list")
    org_members = member_list_action(data_dict={"id": org_id, "object_type": "user"})

    results = []
    for member_id, _, member_role in org_members:
        if role is None or member_role.lower() == role.lower():
            results.append(member_id)

    return results


def user_is_staff_member(user_id: str) -> bool:
    """Check if user is a member of the staff org"""
    memberships_action = toolkit.get_action("organization_list_for_user")
    memberships = memberships_action(context={"user": user_id}, data_dict={})
    portal_staff = toolkit.config.get(
        "ckan.dalrrd_emc_dcpr.portal_staff_organization_name", "sasdi emc staff"
    )
    for group in memberships:
        is_org = group.get("type", "organization") == "organization"
        is_portal_staff = group.get("title").lower() == portal_staff.lower()
        if is_org and is_portal_staff:
            result = True
            break
    else:
        result = False
    return result


def build_pages_nav_main(*args):
    """Reimplementation of ckanext-pages `build_pages_nav_main()`

    This function reimplements the original ckanext-pages in order to overcome
    a bug whereby the groups menu is not removable because of a typo in its route name.

    """

    about_menu = toolkit.asbool(toolkit.config.get("ckanext.pages.about_menu", True))
    group_menu = toolkit.asbool(toolkit.config.get("ckanext.pages.group_menu", True))
    org_menu = toolkit.asbool(
        toolkit.config.get("ckanext.pages.organization_menu", True)
    )

    new_args = []
    for arg in args:
        if arg[0] == "home.about" and not about_menu:
            continue
        if arg[0] == "organization.index" and not org_menu:
            continue
        if arg[0] == "group.index" and not group_menu:
            continue
        new_args.append(arg)

    output = core_build_nav_main(*new_args)

    # do not display any private pages in menu even for sysadmins
    pages_list = toolkit.get_action("ckanext_pages_list")(
        None, {"order": True, "private": False}
    )

    page_name = ""
    is_current_page = toolkit.get_endpoint() in (
        ("pages", "show"),
        ("pages", "blog_show"),
    )

    if is_current_page:
        page_name = toolkit.request.path.split("/")[-1]

    for page in pages_list:
        type_ = "blog" if page["page_type"] == "blog" else "pages"
        name = quote(page["name"])
        title = html_escape(page["title"])
        link = toolkit.h.literal('<a href="/{}/{}">{}</a>'.format(type_, name, title))
        if page["name"] == page_name:
            li = (
                toolkit.literal('<li class="active">') + link + toolkit.literal("</li>")
            )
        else:
            li = toolkit.literal("<li>") + link + toolkit.literal("</li>")
        output = output + li

    return output


def get_featured_datasets():
    search_action = toolkit.get_action("package_search")
    result = search_action(data_dict={"q": "featured:true", "rows": 5})
    return result["results"]


def get_recently_modified_datasets():
    search_action = toolkit.get_action("package_search")
    result = search_action(data_dict={"sort": "metadata_modified desc", "rows": 5})
    return result["results"]


def _pad_geospatial_extent(extent: typing.Dict, padding: float) -> typing.Dict:
    geom = geometry.shape(extent)
    padded = geom.buffer(padding, join_style=geometry.JOIN_STYLE.mitre)
    oriented_padded = geometry.polygon.orient(padded)
    return geometry.mapping(oriented_padded)


def get_status_labels() -> typing.Dict:
    """Get status labels for the DCPR requests"""
    status_labels = {
        constants.DCPRRequestStatus.UNDER_PREPARATION.value: (
            toolkit._("Under preparation"),
            "info",
        ),
        constants.DCPRRequestStatus.AWAITING_NSIF_REVIEW.value: (
            toolkit._("Waiting for NSIF review"),
            "info",
        ),
        constants.DCPRRequestStatus.AWAITING_CSI_REVIEW.value: (
            toolkit._("Waiting for CSI review"),
            "info",
        ),
        constants.DCPRRequestStatus.ACCEPTED.value: (toolkit._("Accepted"), "success"),
        constants.DCPRRequestStatus.REJECTED.value: (toolkit._("Rejected"), "danger"),
    }

    return status_labels


def get_next_intermediate_dcpr_status(current_status: str) -> typing.Optional[str]:
    workflow_order = [
        DCPRRequestStatus.UNDER_PREPARATION,
        DCPRRequestStatus.AWAITING_NSIF_REVIEW,
        DCPRRequestStatus.UNDER_NSIF_REVIEW,
        DCPRRequestStatus.AWAITING_CSI_REVIEW,
        DCPRRequestStatus.UNDER_CSI_REVIEW,
    ]
    result = None
    try:
        current_index = workflow_order.index(DCPRRequestStatus(current_status))
        try:
            next_status = workflow_order[current_index + 1]
            result = next_status.value
        except IndexError:
            # current_index + 1 is out of bounds for the workflow_list
            pass
    except ValueError:
        # input status is not present in the workflow_order list
        pass
    return result


def user_is_dcpr_request_owner(user_id, dcpr_request_id) -> bool:
    request_obj = DCPRRequest.get(dcpr_request_id)
    if request_obj is not None:
        result = user_id == request_obj.owner_user
    else:
        result = False
    return result


def get_org_memberships(user_id: str):
    """Return a list of organizations and roles where the input user is a member"""
    query = (
        model.Session.query(model.Group, model.Member.capacity)
        .join(model.Member, model.Member.group_id == model.Group.id)
        .join(model.User, model.User.id == model.Member.table_id)
        .filter(
            model.User.id == user_id,
            model.Member.state == "active",
            model.Group.is_organization == True,
        )
        .order_by(model.Group.name)
    )
    return query.all()


def get_dcpr_requests_approved_by_nsif(request_origin):
    """
    this feature required by the nsif team,
    as soon as the dcpr_request approved by
    the nsif, it should appear in emc search
    page.
    """
    # if the request awaits for csi, it already passed nsif
    # do to authorization, i had to add a request_oring
    # thus if it's coming from dataset it won't be checked
    # at first stage, but when a user tries to access the
    # request.
    dcpr_requests_approved_by_nsif = toolkit.get_action(
        "dcpr_request_list_awaiting_csi_moderation"
    )({"request_origin": request_origin})
    return dcpr_requests_approved_by_nsif
