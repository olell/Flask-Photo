from flask import Blueprint
from flask import url_for
from flask import session
from flask import redirect
from flask import request
from flask import render_template as flask_render_template

from functools import wraps
import json
from argon2 import PasswordHasher

view = Blueprint("flask_photo", "flask_photo")

config = None

##
#    CONFIG STUFF
##
def write_config():
    with open("photos.json", 'w+') as target: # todo dynameic path to config
        json.dump(config, target, indent=4)

@view.before_app_first_request
def load_config():
    global config
    # This method runs before anything is reachable in the web, so here is the best place to load our config.
    with open("photos.json") as target: # todo dynamic path to config
        config = json.load(target)
    
    if not config["password_crypted"]:
        ph = PasswordHasher()
        config["password"] = ph.hash(config["password"])
        config["password_crypted"] = True

    # Write changes back to config file
    write_config()


def render_template(*args, **kwargs):
    print(config)
    return flask_render_template(*args, **kwargs, conf=config)

##
#     USER MANAGEMENT
## 
@view.route("/login/<redir>", methods=["GET", "POST"])
def login_view(redir):
    if request.method == "GET":
        return render_template("login.jinja")
    else:
        username = request.form.get("username", None)
        password = request.form.get("password", None)

        ph = PasswordHasher()
        if ph.verify(config["password"], password) and config["admin"] == username:
            session["authorized"] = "true"
            return redirect(url_for(redir))
        else:
            return redirect(url_for("flask_photo.login_view", redir=redir))

def requires_login(endpoint):

    @wraps(endpoint)
    def check_login(*args, **kwargs):
        auth = session.get("authorized", None)
        if auth == "true":
            return endpoint(*args, **kwargs)
        return redirect(url_for("flask_photo.login_view", redir=request.endpoint))
    
    return check_login

##
#     ADMIN STUFF
##
@view.route("/admin", methods=["GET", "POST"])
@requires_login
def admin_view():
    if request.method == "GET":
        return render_template("admin.jinja")
    else:
        action = request.form.get("action", None)
        if action is not None:
            
            if action == "add_album":
                album_name = request.form.get("name", None)
                if album_name is not None:
                    album = {
                        "name": album_name,
                        "id": str(hash(album_name)),
                        "description": "New Album",
                        "photos": []
                    }
                    config["content"]["albums"].append(album)
                    write_config()

        return redirect(url_for("flask_photo.admin_view"))

@view.route("/admin_album/<album_id>")
@requires_login
def admin_album_view(album_id):
    album = None
    for album_ in config["content"]["albums"]:
        if album_["id"] == album_id:
            album = album_
    if album is None:
        return "error, album not found..."

    return render_template("album_admin.jinja", album=album)

@view.route("/")
def index():
    return "test123"