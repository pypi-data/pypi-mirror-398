"""
OSITAH validation sub-application

This file contains only the layout definitions
"""

from ositah.apps.validation.callbacks import *
from ositah.utils.menus import DATA_SELECTED_SOURCE_ID, TABLE_TYPE_DUMMY_STORE, team_list_dropdown
from ositah.utils.projects import DATA_SOURCE_HITO


def validation_submenus():
    """
    Build the tabs menus of the validation sub-application

    :return: DBC Tabs
    """

    return dbc.Tabs(
        [
            dbc.Tab(
                id=TAB_ID_DECLARATION_STATS,
                tab_id=TAB_ID_DECLARATION_STATS,
                label="Statistiques",
            ),
            dbc.Tab(
                id=TAB_ID_VALIDATION,
                tab_id=TAB_ID_VALIDATION,
                label="Déclarations Effectuées",
            ),
            dbc.Tab(
                id=TAB_ID_MISSING_AGENTS,
                tab_id=TAB_ID_MISSING_AGENTS,
                label="Déclarations Manquantes",
            ),
        ],
        id=VALIDATION_TAB_MENU_ID,
    )


def validation_layout():
    """
    Build the layout for this application, after reading the data if necessary.

    :return: application layout
    """

    from ositah.utils.hito_db_model import (
        OSITAHProjectDeclaration,
        OSITAHValidation,
        OSITAHValidationPeriod,
    )

    db = get_db()

    OSITAHValidationPeriod.__table__.create(db.session.bind, checkfirst=True)
    OSITAHValidation.__table__.create(db.session.bind, checkfirst=True)
    OSITAHProjectDeclaration.__table__.create(db.session.bind, checkfirst=True)

    return html.Div(
        [
            html.H1("Affichage et validation des déclarations"),
            team_list_dropdown(),
            dcc.Store(id=DATA_SELECTED_SOURCE_ID, data=DATA_SOURCE_HITO),
            html.Div(
                validation_submenus(),
                id="validation-submenus",
                style={"marginTop": "3em"},
            ),
            dcc.Store(id=VALIDATION_LOAD_INDICATOR_ID, data=0),
            dcc.Store(id=VALIDATION_SAVED_INDICATOR_ID, data=0),
            dcc.Store(
                id=VALIDATION_DECLARATIONS_SELECTED_ID,
                data=VALIDATION_DECLARATIONS_SELECT_ALL,
            ),
            dcc.Store(id=VALIDATION_SAVED_ACTIVE_TAB_ID, data=""),
            # The following dcc.Store coupled with tables must be created in the layout for
            # the callback to work
            dcc.Store(id={"type": TABLE_TYPE_DUMMY_STORE, "id": TABLE_ID_VALIDATION}, data=0),
            dcc.Store(
                id={"type": TABLE_TYPE_DUMMY_STORE, "id": TABLE_ID_MISSING_AGENTS},
                data=0,
            ),
            dcc.Store(
                id={"type": TABLE_TYPE_DUMMY_STORE, "id": TABLE_ID_DECLARATION_STATS},
                data=0,
            ),
        ]
    )
