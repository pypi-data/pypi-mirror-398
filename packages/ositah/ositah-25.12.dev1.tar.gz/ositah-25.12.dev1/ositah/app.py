# Dash app initialization

import os

import dash_bootstrap_components as dbc
from dash import Dash
from flask import Flask

APP_NAME = __name__
FLASK_TEMPLATES_DIR = f"{os.path.dirname(__file__)}/templates"

app = Dash(
    APP_NAME,
    server=Flask(APP_NAME, template_folder=FLASK_TEMPLATES_DIR),
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
