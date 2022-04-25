import logging
import typing

from ckan.plugins import toolkit
from ...model import dcpr_request as dcpr_request
from ...constants import DCPRRequestStatus

logger = logging.getLogger(__name__)


def dcpr_request_list_private_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
):
    """Authorize listing private DCPR requests.

    Only users that are members of an organization are allowed to have private DCPR
    requests.

    """
    # FIXME: Implement this
    return {"success": False}


@toolkit.auth_allow_anonymous_access
def dcpr_request_list_public_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    """Authorize listing public DCPR requests"""
    return {"success": True}


def dcpr_request_list_pending_csi_auth():
    """Authorize listing DCPR requests which are under evaluation by CSI"""
    # FIXME: Implement this
    return {"success": False}


def dcpr_request_list_pending_nsif_auth():
    """Authorize listing DCPR requests which are under evaluation by NSIF"""
    # FIXME: Implement this
    return {"success": False}


def dcpr_report_create_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_report_create auth")
    user = context["auth_user_obj"]

    # Only allow creation of dcpr report if there is a user logged in.
    if user:
        return {"success": True}
    return {"success": False}


def dcpr_request_create_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    """Authorize DCPR request creation.

    Creation of DCPR requests is reserved for logged in users that have been granted
    membership of an organization.

    NOTE: The implementation does not need to check if the user is logged in because
    CKAN already does that for us, as per:

    https://docs.ckan.org/en/2.9/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IAuthFunctions

    """

    logger.debug("Inside the dcpr_request_create_auth")
    logger.info(f"{context=}")
    logger.info(f"{data_dict=}")
    db_user = context["auth_user_obj"]
    member_of_orgs = len(db_user.get_groups()) > 0
    result = {"success": member_of_orgs}
    logger.info(f"{result=}")
    return result


@toolkit.auth_allow_anonymous_access
def dcpr_request_show_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_show auth")
    if not data_dict:
        return {"success": False}

    request_id = data_dict.get("id", None)

    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)

    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    show_request = (
        request_obj.status != DCPRRequestStatus.UNDER_PREPARATION.value
    ) and (request_obj.status != DCPRRequestStatus.AWAITING_NSIF_REVIEW.value)
    return {"success": show_request}


def dcpr_request_update_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_update auth")

    user = context["auth_user_obj"]

    if not user or not data_dict:
        return {"success": False}

    request_id = data_dict.get("id", None)
    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)

    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    owner = user.id == request_obj.owner_user
    request_in_preparation = (
        request_obj.status == DCPRRequestStatus.UNDER_PREPARATION.value
    )

    nsif_reviewer = toolkit.h["emc_user_is_org_member"]("nsif", user, role="editor")
    csi_reviewer = toolkit.h["emc_user_is_org_member"]("csi", user, role="editor")

    request_escalated_to_csi = (
        request_obj.status == DCPRRequestStatus.AWAITING_CSI_REVIEW.value
    )
    request_submitted = (
        request_obj.status == DCPRRequestStatus.AWAITING_NSIF_REVIEW.value
    )

    success = (
        (owner and request_in_preparation)
        or (csi_reviewer and request_escalated_to_csi)
        or (nsif_reviewer and request_submitted)
    )

    return {"success": success}


def dcpr_request_submit_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_submit auth")

    user = context["auth_user_obj"]

    if not user or not data_dict:
        return {"success": False}

    request_id = data_dict.get("id", None)
    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)

    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    owner = user.id == request_obj.owner_user
    request_in_preparation = (
        request_obj.status == DCPRRequestStatus.UNDER_PREPARATION.value
    )

    return {"success": (owner and request_in_preparation)}


def dcpr_request_escalate_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_escalate auth")

    user = context["auth_user_obj"]

    if not user or not data_dict:
        return {"success": False}

    request_id = data_dict.get("request_id", None)
    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)

    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    nsif_reviewer = toolkit.h["emc_user_is_org_member"]("nsif", user, role="editor")
    request_submitted = (
        request_obj.status == DCPRRequestStatus.AWAITING_NSIF_REVIEW.value
    )

    return {"success": nsif_reviewer and request_submitted}


def dcpr_request_accept_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_accept auth")

    user = context["auth_user_obj"]

    if not user or not data_dict:
        return {"success": False}

    request_id = data_dict.get("request_id", None)
    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)

    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    csi_reviewer = toolkit.h["emc_user_is_org_member"]("csi", user, role="editor")
    request_escalated_to_csi = (
        request_obj.status == DCPRRequestStatus.AWAITING_CSI_REVIEW.value
    )

    return {
        "success": csi_reviewer and request_escalated_to_csi,
    }


def dcpr_request_reject_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_reject auth")

    user = context["auth_user_obj"]

    if not user or not data_dict:
        return {"success": False}

    request_id = data_dict.get("request_id", None)
    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)

    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    nsif_reviewer = toolkit.h["emc_user_is_org_member"]("nsif", user, role="editor")
    csi_reviewer = toolkit.h["emc_user_is_org_member"]("csi", user, role="editor")

    request_escalated_to_csi = (
        request_obj.status == DCPRRequestStatus.AWAITING_CSI_REVIEW.value
    )
    request_submitted = (
        request_obj.status == DCPRRequestStatus.AWAITING_NSIF_REVIEW.value
    )

    return {
        "success": (csi_reviewer and request_escalated_to_csi)
        or (nsif_reviewer and request_submitted)
    }


def dcpr_request_edit_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_edit auth")
    user = context["auth_user_obj"]

    if not user or not data_dict:
        return {"success": False}

    request_id = data_dict.get("id", None)

    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)

    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    owner = user.id == request_obj.owner_user
    nsif_reviewer = toolkit.h["emc_user_is_org_member"]("nsif", user, role="editor")
    csi_reviewer = toolkit.h["emc_user_is_org_member"]("csi", user, role="editor")

    if not owner and not nsif_reviewer and not csi_reviewer:
        return {"success": False}

    return {"success": True}


def dcpr_request_delete_auth(
    context: typing.Dict, data_dict: typing.Optional[typing.Dict] = None
) -> typing.Dict:
    logger.debug("Inside the dcpr_request_delete auth")

    user = context["auth_user_obj"]

    if not user or not data_dict:
        return {"success": False}

    request_id = data_dict.get("request_id", None)

    request_obj = dcpr_request.DCPRRequest.get(csi_reference_id=request_id)
    if not request_obj:
        return {"success": False, "msg": toolkit._("Request not found")}

    owner = user.get("id") == request_obj.owner_user
    request_in_preparation = (
        request_obj.status == DCPRRequestStatus.UNDER_PREPARATION.value
    )

    if not owner or not request_in_preparation:
        return {"success": False}

    return {"success": True}
