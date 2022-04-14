import logging

from flask import Blueprint, redirect, request
from ckan.plugins import toolkit
from ckan.logic import clean_dict, parse_params, tuplize_dict
import ckan.lib.navl.dictization_functions as dict_fns

from ..helpers import get_status_labels
from ..model.dcpr_request import DCPRRequestOrganizationLevel, DCPRRequestUrgency

logger = logging.getLogger(__name__)

dcpr_blueprint = Blueprint(
    "dcpr", __name__, template_folder="templates", url_prefix="/dcpr"
)


@dcpr_blueprint.route("/")
def dcpr_home():
    logger.debug("Inside the dcpr_home view")
    existing_requests = toolkit.get_action("dcpr_request_list")(data_dict={})

    extra_vars = {}
    extra_vars["dcpr_requests"] = existing_requests
    extra_vars["request_status"] = get_status_labels()

    return toolkit.render("dcpr/index.html", extra_vars=extra_vars)


@dcpr_blueprint.route("/request/new", methods=["GET", "POST"])
def dcpr_request_new():
    logger.debug("Inside the dcpr_new_request view")
    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }
    extra_vars = {}
    organizations = toolkit.get_action("organization_list")(context, {})
    organizations = [{"value": org, "text": org} for org in organizations]

    organizations_levels = [
        {"value": level.value, "text": level.value}
        for level in DCPRRequestOrganizationLevel
    ]
    data_urgency = [
        {"value": level.value, "text": level.value} for level in DCPRRequestUrgency
    ]

    extra_vars["dcpr_request"] = None
    extra_vars["organizations"] = organizations
    extra_vars["organizations_levels"] = organizations_levels
    extra_vars["data_urgency"] = data_urgency

    if request.method == "POST":
        try:
            data_dict = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
            )
            data_dict["owner_user"] = toolkit.g.userobj.id

        except dict_fns.DataError:
            return toolkit.base.abort(400, toolkit._("Integrity Error"))
        try:
            dcpr_request = toolkit.get_action("dcpr_request_create")(context, data_dict)

            url = toolkit.h.url_for(
                "{0}.dcpr_request_show".format("dcpr"),
                request_id=dcpr_request.csi_reference_id,
            )
            return toolkit.h.redirect_to(url)

        except toolkit.NotAuthorized:
            return toolkit.base.abort(
                403, toolkit._("Unauthorized to create DCPR request")
            )
        except toolkit.ObjectNotFound as e:
            return toolkit.base.abort(404, toolkit._("DCPR request not found"))
        except toolkit.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary

            request.method = "GET"
            return dcpr_request_edit(
                None, data=data_dict, errors=errors, error_summary=error_summary
            )

        url = toolkit.h.url_for(
            "{0}.dcpr_request_show".format("dcpr"),
            request_id=dcpr_request.csi_reference_id,
        )
        return toolkit.h.redirect_to(url)

    else:
        try:
            toolkit.check_access("dcpr_request_create_auth", context)
        except toolkit.NotAuthorized:
            return toolkit.base.abort(
                403,
                toolkit._("User %r not authorized to create DCPR requests")
                % (toolkit.g.user),
            )

        return toolkit.render("dcpr/new.html", extra_vars=extra_vars)


@dcpr_blueprint.route("/request/<request_id>")
def dcpr_request_show(request_id):
    logger.debug("Inside the dcpr_request_show view")
    data_dict = {"id": request_id}
    extra_vars = {}
    extra_vars["request_status"] = get_status_labels()

    nsif_reviewer = toolkit.h["emc_user_is_org_member"](
        "nsif", toolkit.g.userobj, role="editor"
    )
    csi_reviewer = toolkit.h["emc_user_is_org_member"](
        "csi", toolkit.g.userobj, role="editor"
    )

    extra_vars["nsif_reviewer"] = nsif_reviewer
    extra_vars["csi_reviewer"] = csi_reviewer

    try:
        dcpr_request = toolkit.get_action("dcpr_request_show")(data_dict=data_dict)
        request_owner = (
            dcpr_request["owner_user"] == toolkit.g.userobj.id
            if toolkit.g.userobj
            else False
        )

        extra_vars["dcpr_request"] = dcpr_request
        extra_vars["request_owner"] = request_owner

    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        return toolkit.base.abort(404, toolkit._("Request not found"))

    return toolkit.render("dcpr/show.html", extra_vars=extra_vars)


@dcpr_blueprint.route("/request/update/<request_id>", methods=["POST"])
def dcpr_request_update(request_id, data=None, errors=None, error_summary=None):
    logger.debug("Inside the dcpr_request_edit view")
    extra_vars = {}
    extra_vars["errors"] = errors

    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }

    try:
        data_dict = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
        )
        data_dict["csi_moderator"] = None
        data_dict["nsif_reviewer"] = None
        data_dict["id"] = request_id

    except dict_fns.DataError:
        return toolkit.base.abort(400, toolkit._("Integrity Error"))
    try:
        toolkit.get_action("dcpr_request_update")(context, data_dict)

        url = toolkit.h.url_for(
            "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
        )
        return toolkit.h.redirect_to(url)

    except toolkit.NotAuthorized as e:
        return toolkit.base.abort(
            403,
            toolkit._("Unauthorized to perfom the action, %s") % e,
        )
    except toolkit.ObjectNotFound as e:
        return toolkit.base.abort(404, toolkit._("DCPR request not found"))
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary

        request.method = "GET"
        return dcpr_request_edit(
            data_dict.get("request_id", None), data_dict, errors, error_summary
        )

    url = toolkit.h.url_for(
        "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
    )
    return toolkit.h.redirect_to(url)


@dcpr_blueprint.route("/request/submit/", methods=["POST"])
@dcpr_blueprint.route("/request/submit/<request_id>", methods=["POST"])
def dcpr_request_submit(request_id, data=None, errors=None, error_summary=None):
    logger.debug("Inside the dcpr_request_submit view")
    extra_vars = {}
    extra_vars["errors"] = errors

    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }

    try:
        data_dict = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
        )
        data_dict["csi_moderator"] = None
        data_dict["nsif_reviewer"] = None
        data_dict["id"] = request_id

    except dict_fns.DataError:
        return toolkit.base.abort(400, toolkit._("Integrity Error"))
    try:
        if not request_id:
            dcpr_request = toolkit.get_action("dcpr_request_create")(context, data_dict)
            request_id = dcpr_request.csi_reference_id

        toolkit.get_action("dcpr_request_submit")(context, data_dict)

        url = toolkit.h.url_for(
            "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
        )
        return toolkit.h.redirect_to(url)

    except toolkit.NotAuthorized as e:
        return toolkit.base.abort(
            403,
            toolkit._("Unauthorized to perfom the action, %s") % e,
        )
    except toolkit.ObjectNotFound as e:
        return toolkit.base.abort(404, toolkit._("DCPR request not found"))
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary

        request.method = "GET"
        return dcpr_request_edit(
            data_dict.get("request_id", None), data_dict, errors, error_summary
        )

    url = toolkit.h.url_for(
        "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
    )
    return toolkit.h.redirect_to(url)


@dcpr_blueprint.route("/request/escalate/<request_id>", methods=["POST"])
def dcpr_request_escalate(request_id, data=None, errors=None, error_summary=None):
    logger.debug("Inside the dcpr_request_edit view")
    data_dict = {"id": request_id}
    extra_vars = {}
    extra_vars["errors"] = errors

    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }

    try:
        data_dict = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
        )
        data_dict["csi_moderator"] = None

    except dict_fns.DataError:
        return toolkit.base.abort(400, toolkit._("Integrity Error"))
    try:
        toolkit.get_action("dcpr_request_escalate")(context, data_dict)

        url = toolkit.h.url_for(
            "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
        )
        return toolkit.h.redirect_to(url)

    except toolkit.NotAuthorized as e:
        return toolkit.base.abort(
            403,
            toolkit._("Unauthorized to perfom the action, %s") % e,
        )
    except toolkit.ObjectNotFound as e:
        return toolkit.base.abort(404, toolkit._("DCPR request not found"))
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary

        request.method = "GET"
        return dcpr_request_edit(
            data_dict.get("request_id", None), data_dict, errors, error_summary
        )

    url = toolkit.h.url_for(
        "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
    )
    return toolkit.h.redirect_to(url)


@dcpr_blueprint.route("/request/accept/<request_id>", methods=["POST"])
def dcpr_request_accept(request_id, data=None, errors=None, error_summary=None):
    logger.debug("Inside the dcpr_request_accept view")
    data_dict = {"id": request_id}
    extra_vars = {}
    extra_vars["errors"] = errors

    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }

    try:
        data_dict = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
        )

    except dict_fns.DataError:
        return toolkit.base.abort(400, toolkit._("Integrity Error"))
    try:
        toolkit.get_action("dcpr_request_accept")(context, data_dict)

        url = toolkit.h.url_for(
            "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
        )
        return toolkit.h.redirect_to(url)

    except toolkit.NotAuthorized as e:
        return toolkit.base.abort(
            403,
            toolkit._("Unauthorized to perfom the action, %s") % e,
        )
    except toolkit.ObjectNotFound as e:
        return toolkit.base.abort(404, toolkit._("DCPR request not found"))
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary

        request.method = "GET"
        return dcpr_request_edit(
            data_dict.get("request_id", None), data_dict, errors, error_summary
        )

    url = toolkit.h.url_for(
        "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
    )
    return toolkit.h.redirect_to(url)


@dcpr_blueprint.route("/request/reject/<request_id>", methods=["POST"])
def dcpr_request_reject(request_id, data=None, errors=None, error_summary=None):
    logger.debug("Inside the dcpr_request_reject view")
    data_dict = {"id": request_id}
    extra_vars = {}
    extra_vars["errors"] = errors

    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }

    try:
        data_dict = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
        )

    except dict_fns.DataError:
        return toolkit.base.abort(400, toolkit._("Integrity Error"))
    try:
        toolkit.get_action("dcpr_request_reject")(context, data_dict)

        url = toolkit.h.url_for(
            "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
        )
        return toolkit.h.redirect_to(url)

    except toolkit.NotAuthorized as e:
        return toolkit.base.abort(
            403,
            toolkit._("Unauthorized to perfom the action, %s") % e,
        )
    except toolkit.ObjectNotFound as e:
        return toolkit.base.abort(404, toolkit._("DCPR request not found"))
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary

        request.method = "GET"
        return dcpr_request_edit(
            data_dict.get("request_id", None), data_dict, errors, error_summary
        )

    url = toolkit.h.url_for(
        "{0}.dcpr_request_show".format("dcpr"), request_id=request_id
    )
    return toolkit.h.redirect_to(url)


@dcpr_blueprint.route("/request/edit/<request_id>", methods=["GET"])
def dcpr_request_edit(request_id, data=None, errors=None, error_summary=None):
    logger.debug("Inside the dcpr_request_edit view")
    data_dict = {"id": request_id}
    extra_vars = {}
    extra_vars["errors"] = errors

    organizations = toolkit.get_action("organization_list")({}, {})
    organizations = [{"value": org, "text": org} for org in organizations]

    organizations_levels = [
        {"value": level.value, "text": level.value}
        for level in DCPRRequestOrganizationLevel
    ]
    data_urgency = [
        {"value": level.value, "text": level.value} for level in DCPRRequestUrgency
    ]
    extra_vars["organizations"] = organizations
    extra_vars["organizations_levels"] = organizations_levels
    extra_vars["data_urgency"] = data_urgency

    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }

    try:
        if request_id is not None:
            dcpr_request = toolkit.get_action("dcpr_request_show")(data_dict=data_dict)
            extra_vars["dcpr_request"] = dcpr_request
        elif data is not None:
            extra_vars["dcpr_request"] = data
            extra_vars["error_summary"] = error_summary

        nsif_reviewer = toolkit.h["emc_user_is_org_member"](
            "nsif", toolkit.g.userobj, role="editor"
        )
        csi_reviewer = toolkit.h["emc_user_is_org_member"](
            "csi", toolkit.g.userobj, role="editor"
        )
        extra_vars["nsif_reviewer"] = nsif_reviewer
        extra_vars["csi_reviewer"] = csi_reviewer

    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        return toolkit.base.abort(404, toolkit._("Request not found"))

    try:
        toolkit.check_access("dcpr_request_edit_auth", context, data_dict)

    except toolkit.NotAuthorized:
        return toolkit.base.abort(
            403,
            toolkit._("User %r not authorized to edit the requested DCPR request")
            % (toolkit.g.user),
        )

    return toolkit.render("dcpr/edit.html", extra_vars=extra_vars)


@dcpr_blueprint.route("/request/delete/<request_id>", methods=["GET", "POST"])
def dcpr_request_delete(request_id, errors=None, error_summary=None):
    logger.debug("Inside the dcpr_request_delete view")
    data_dict = {"request_id": request_id}
    extra_vars = {}

    context = {
        "user": toolkit.g.user,
        "auth_user_obj": toolkit.g.userobj,
    }

    if request.method == "GET":
        try:
            toolkit.check_access(
                "dcpr_request_delete_auth", context, {"request_id": request_id}
            )
        except toolkit.NotAuthorized:
            return toolkit.base.abort(
                403,
                toolkit._("User %r not authorized to delete DCPR requests")
                % (toolkit.g.user),
            )

        return toolkit.render("dcpr/delete.html", extra_vars=extra_vars)

    else:
        try:
            dcpr_request = toolkit.get_action("dcpr_request_delete")(context, data_dict)

            url = toolkit.h.url_for("{0}.dcpr_home".format("dcpr"))
            return toolkit.h.redirect_to(url)

        except toolkit.NotAuthorized as e:
            return toolkit.base.abort(
                403,
                toolkit._("Unauthorized to perfom the action, %s") % e,
            )
        except toolkit.ObjectNotFound as e:
            return toolkit.base.abort(404, toolkit._("DCPR request not found"))
        except toolkit.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return dcpr_request_edit(
                dcpr_request.csi_reference_id, errors, error_summary
            )

        url = toolkit.h.url_for("{0}.dcpr_home".format("dcpr"))
        return toolkit.h.redirect_to(url)
