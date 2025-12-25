# Module to handle user login with flask-multipass, a multi-backend authentication module for Flask
# The code is largely based on a simplified version of what Indico is doing and is focused on using
# LDAP (IJCLab ActiveDirectory) as the backend.
#
# There is no attempt to store session data in a database.

import functools
import json
from urllib.parse import urlparse
from uuid import uuid1

from flask import flash, redirect, request, session
from flask_multipass import InvalidCredentials, Multipass, NoSuchUser

from ositah.utils.utils import GlobalParams

# Redirect URL for login and logout
LOGIN_URL = "/login"
LOGOUT_URL = "/logout"


# Session validity duration (in hours), i.e. max time since the last use
SESSION_MAX_DURATION = 4


# List of authenticated users
user_list = {}
identity_list = {}


class User:
    def __init__(self, first_name=None, last_name=None, email=None):
        self._id = uuid1()
        self._firstname = first_name
        self._lastname = last_name
        self._email = email
        self._identities = []

    def add_identity(self, identity):
        self._identities.append(identity)

    @property
    def identities(self):
        return self._identities

    @property
    def email(self):
        return self._email

    def get_first_identity(self):
        if len(self._identities) >= 1:
            return self._identities[0]
        else:
            return Exception(f"No identity defined for user '{self.email}'")

    @property
    def id(self):
        return self._id


class Identity:
    def __init__(self, provider=None, identifier=None):
        self._id = identifier
        self._provider = provider
        self._multipass_data = None

    @property
    def id(self):
        return self._id

    @property
    def multipass_data(self):
        return self._multipass_data

    @multipass_data.setter
    def multipass_data(self, data):
        self._multipass_data = data

    @property
    def provider(self):
        return self._provider


class OSITAHMultipass(Multipass):
    def init_app(self, app):
        super(OSITAHMultipass, self).init_app(app)
        with app.app_context():
            self._check_default_provider()

    def _check_default_provider(self):
        # Ensure that there is maximum one sync provider
        sync_providers = [
            p for p in self.identity_providers.values() if p.settings.get("synced_fields")
        ]
        if len(sync_providers) > 1:
            raise ValueError("There can only be one sync provider.")
        # Ensure that there is exactly one form-based default auth provider
        auth_providers = list(self.auth_providers.values())
        external_providers = [p for p in auth_providers if p.is_external]
        local_providers = [p for p in auth_providers if not p.is_external]
        if any(p.settings.get("default") for p in external_providers):
            raise ValueError("The default provider cannot be external")
        if all(p.is_external for p in auth_providers):
            return
        default_providers = [p for p in auth_providers if p.settings.get("default")]
        if len(default_providers) > 1:
            raise ValueError("There can only be one default auth provider")
        elif not default_providers:
            if len(local_providers) == 1:
                local_providers[0].settings["default"] = True
            else:
                raise ValueError("There is no default auth provider")

    def handle_auth_error(self, exc, redirect_to_login=False):
        if isinstance(exc, (NoSuchUser, InvalidCredentials)):
            print("Invalid credentials")
        else:
            exc_str = str(exc)
            print(
                "Authentication via %s failed: %s (%r)",
                exc.provider.name if exc.provider else None,
                exc_str,
                exc.details,
            )
        return super(OSITAHMultipass, self).handle_auth_error(
            exc, redirect_to_login=redirect_to_login
        )


def configure_multipass_ldap(app, provider_title):
    """
    Configure Flask_multipass from configuration. Inspired from Indico and its configuration file.
    Required flask_multipass with PR #42.

    :param app: Flask app
    :param provider_title: text associated with the auth/identity provider
    :return: none
    """

    global_params = GlobalParams()
    config = global_params.ldap

    if not config or len(config) == 0:
        raise Exception("Missing LDAP configuration")

    ldap_config = {
        "uri": config["uri"],
        "bind_dn": config["bind_dn"],
        "bind_password": config["password"],
        "timeout": 30,
        "verify_cert": True,
        "page_size": 10000,
        "uid": "sAMAccountName",
        "user_base": config["base_dn"],
        "user_filter": "(objectcategory=user)",
    }

    auth_provider = {
        "ldap": {
            "type": "ldap",
            "title": provider_title,
            "ldap": ldap_config,
        },
    }

    identity_provider = {
        "ldap": {
            "type": "ldap",
            "title": provider_title,
            "ldap": ldap_config,
            "identifier_field": "mail",
            "accepted_users": "all",
            "mapping": {
                "first_name": "givenName",
                "last_name": "sn",
                "email": "mail",
                "affiliation": "company",
                "phone": "telephoneNumber",
            },
            "trusted_email": True,
        },
    }

    app.config["MULTIPASS_AUTH_PROVIDERS"] = auth_provider
    app.config["MULTIPASS_IDENTITY_PROVIDERS"] = identity_provider
    app.config["MULTIPASS_PROVIDER_MAP"] = {"ldap": "ldap"}
    app.config["MULTIPASS_IDENTITY_INFO_KEYS"] = {"first_name", "last_name", "email"}
    app.config["MULTIPASS_LOGIN_FORM_TEMPLATE"] = "login_form.html"
    app.config["MULTIPASS_SUCCESS_ENDPOINT"] = "/"
    app.config["MULTIPASS_FAILURE_MESSAGE"] = "Login failed: {error}"


multipass = OSITAHMultipass()


@multipass.identity_handler
def identity_handler(identity_info):
    if identity_info.identifier in identity_list:
        user = identity_list[identity_info.identifier]
        identity = user.get_first_identity()
    else:
        if identity_info.data["email"] in user_list:
            user = user_list[identity_info.data["email"]]
        else:
            user = User(**identity_info.data.to_dict())
            user_list[user.email] = user
        identity = Identity(
            provider=identity_info.provider.name, identifier=identity_info.identifier
        )
        user.add_identity(identity)
        identity_list[identity.id] = user
    identity.multipass_data = json.dumps(identity_info.multipass_data)
    session["user_id"] = identity.id
    flash("Received IdentityInfo: {}".format(identity_info), "success")


def login_required(view):
    """
    A decorator to require login on Flask views

    :param view: a function
    :return: decorated function
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        redirect_path = urlparse(request.base_url).path
        if len(redirect_path) == 0:
            redirect_path = "/"
        if "user_id" not in session:
            if redirect_path != "/favicon.ico":
                return redirect(f"{LOGIN_URL}?next={redirect_path}")
        elif redirect_path == LOGOUT_URL:
            remove_session()
            return multipass.logout("/", clear_session=True)

        return view(**kwargs)

    return wrapped_view


def protect_views(app):
    for view_func in app.server.view_functions:
        if view_func.startswith("/<path:path>"):
            app.server.view_functions[view_func] = login_required(
                app.server.view_functions[view_func]
            )

    return app


def remove_session():
    """
    Remove a session from the database and do additional session cleanup.

    :return: None
    """

    from sqlalchemy import delete

    from ositah.utils.hito_db import get_db
    from ositah.utils.hito_db_model import OSITAHSession

    global_params = GlobalParams()

    if "uid" in session:
        del global_params.session_data

        if session["user_id"] in identity_list:
            del user_list[identity_list[session["user_id"]].email]
            del identity_list[session["user_id"]]
        else:
            print(
                (
                    f"WARNING: attempt to delete a non-existing user/identity"
                    f" {session['uid']} (user={session['user_id']})"
                )
            )

        if "user_email" in session:
            sql_cmd = delete(OSITAHSession).where(
                OSITAHSession.id == session["uid"],
                OSITAHSession.email == session["user_email"],
            )
            db = get_db()
            db.session.execute(sql_cmd)
            db.session.commit()
