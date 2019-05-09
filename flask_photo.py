from flask import Blueprint
from flask import url_for
from flask import session
from flask import redirect
from flask import request
from flask import render_template as flask_render_template
from werkzeug.utils import secure_filename

import os
from functools import wraps
import json
from argon2 import PasswordHasher
import random
import string

view = Blueprint("flask_photo", "flask_photo")

config = None

##
#    HELPER METHODS
##

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.hexdigits
    return ''.join(random.choice(letters) for i in range(stringLength))

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
                        "id": randomString(16),
                        "description": "New Album",
                        "photos": []
                    }
                    config["content"]["albums"].append(album)
                    write_config()

        return redirect(url_for("flask_photo.admin_view"))

@view.route("/admin_album/<album_id>", methods=["GET", "POST"])
@requires_login
def admin_album_view(album_id):
    album = None
    for album_ in config["content"]["albums"]:
        if album_["id"] == album_id:
            album = album_
    if album is None:
        return "error, album not found..."

    if request.method == "GET":
        return render_template("album_admin.jinja", album=album)
    else:
        action = request.form.get("action", None)
        if action is not None:
            if action == "update_album_info":
                new_name = request.form.get("name", None)
                new_desc = request.form.get("description", None)
                album["name"] = new_name
                album["description"] = new_desc
                write_config()
            if action == "add_photo":
                file = request.files.get('file', None)
                description = request.form.get("desc", None)
                if file is not None and file.filename:
                    iid = randomString(16)
                    filename = secure_filename(file.filename)
                    ext = filename.split(".")[-1]
                    path = os.path.join("static/uploads/", iid + "." + ext)
                    file.save(path)

                    album["photos"].append({
                        "name": filename,
                        "description": description,
                        "id": iid,
                        "url": path
                    })
                    write_config()

        return redirect(url_for("flask_photo.admin_album_view", album_id=album_id))

@view.route("/")
def index():
    return "test123"