import uuid
from flask import Blueprint, request, jsonify
from ckan.plugins import toolkit
from ckan import model
from ckan.common import c
from datetime import date, datetime

saved_searches_blueprint = Blueprint(
    "saved_searches",
    __name__,
    template_folder="templates",
    url_prefix="/saved_searches",
)


@saved_searches_blueprint.route("/")
def index():
    return toolkit.render("saved_searches.html")


@saved_searches_blueprint.route("/save_search", methods=["GET", "POST"])
def save_current_search():
    """
    save the current search
    query with user_id
    """
    query = request.json
    user_id = c.userobj.id
    saved_search_id = uuid.uuid4()
    saved_search_title = _get_saved_search_title(query)
    q = f""" insert into saved_searches values('{saved_search_id}', '{user_id}', '{query}', '{saved_search_title}','{datetime.now().strftime("%m/%d/%Y%H:%M:%S")}') """
    result = model.Session.execute(q)
    model.Session.commit()
    return jsonify({"status": 200})


def _get_saved_search_title(query):
    """
    takes the title from an input
    if the title is "" it returns
    the current date.
    """
    query_str = "q=" in query
    query_input = query.split("&", 1)[0]
    current_date = date.today().strftime("%m/%d/%Y")
    if not query_str:
        return "Query saved on " + current_date.replace("/", "-")
    else:
        return query_input.replace("q=", "") + " " + current_date.replace("/", "-")
