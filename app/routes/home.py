from flask import Blueprint, render_template, request

home_bp = Blueprint("home", __name__)
document_bp=Blueprint("document",__name__)


@home_bp.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")

@document_bp.route("/document")
def document():
    return render_template("documentation.html")