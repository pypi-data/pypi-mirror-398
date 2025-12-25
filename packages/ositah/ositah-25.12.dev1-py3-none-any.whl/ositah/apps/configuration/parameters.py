"""
Parameters related to Dash components in the Configuration sub-application
"""

CONFIGURATION_TAB_MENU_ID = "configuration-tabs"
TAB_ID_NSIP_PROJECT_SYNC = "nsip-project-sync-tab"
TAB_ID_ACTIVITY_TEAMS = "config-activity-teams-tab"
TAB_ID_DECLARATION_PERIODS = "config-validation-period-tab"
TAB_ID_PROJECT_MGT = "config-project-mgt-tab"

ACTIVITY_TEAMS_MASTERPROJECTS_ID = "config-activity-teams-masterprojects"
ACTIVITY_TEAMS_PROJECTS_ID = "config-activity-teams-projects"
ACTIVITY_TEAMS_LAB_TEAMS_ID = "config-activity-teams-lab-teams"
ACTIVITY_TEAMS_SELECTED_TEAMS_ID = "config-activity-teams-selected-teams"
ACTIVITY_TEAMS_BUTTON_ADD_ID = "config-activity-teams-add-team"
ACTIVITY_TEAMS_BUTTON_CANCEL_ID = "config-activity-teams-cancel-team"
ACTIVITY_TEAMS_BUTTON_REMOVE_ID = "config-activity-teams-remove-team"
ACTIVITY_TEAMS_BUTTON_UPDATE_ID = "config-activity-teams-update-button"
ACTIVITY_TEAMS_PROJECT_ACTIVITY_ID = "config-activity-teams-is-project"
ACTIVITY_TEAMS_ADDED_TEAMS_ID = "config-activity-teams-added-teams"
ACTIVITY_TEAMS_REMOVED_TEAMS_ID = "config-activity-teams-removed-teams"
ACTIVITY_TEAMS_STATUS_ID = "config-activity-teams-status-msg"
ACTIVITY_TEAMS_RESET_INDICATOR_ID = "config-activity-teams-reset-indicator"
ACTIVITY_TEAMS_LIST_MAX_SIZE = 10
ACTIVITY_TEAMS_LIST_BOX_WIDTH = 5
# Attempt to reduce list box width on very large display (2500+px) but unfortunately
# Bootstrap xxl is 1400+px thus including full HD. Not clear how to tune mediaclass definitions.
ACTIVITY_TEAMS_LIST_BOX_WIDTH_XXL = 5
ACTIVITY_TEAMS_LIST_BOX_INTERVAL = 1

DECLARATION_PERIOD_END_DATE_ID = "config-declaration-period-end"
DECLARATION_PERIOD_NAME_ID = "config-declaration-period-name"
DECLARATION_PERIOD_PARAMS_ID = "config-declaration-period-params"
DECLARATION_PERIOD_START_DATE_ID = "config-declaration-period-start"
DECLARATION_PERIOD_VALIDATION_DATE_ID = "config-declaration-period-validation"
DECLARATION_PERIODS_ID = "config-declaration-periods"
DECLARATION_PERIODS_CREATE_NEW_ID = "config-declaration-periods-create-new"
DECLARATION_PERIODS_CREATE_DIV_ID = "config-declaration-periods-create-div"
DECLARATION_PERIODS_CREATE_CLICK_ID = "config-declaration-periods-create-click-saved"
DECLARATION_PERIODS_SAVE_NEW_ID = "config-declaration-periods-save-new"
DECLARATION_PERIODS_SAVE_DIV_ID = "config-declaration-periods-save-div"
DECLARATION_PERIODS_STATUS_ID = "config-declaration-periods-status"
DECLARATION_PERIODS_STATUS_HIDDEN_ID = "config-declaration-periods-status-hidden"
DECLARATION_PERIODS_STATUS_VISIBLE_ID = "config-declaration-periods-status-visible"
DECLARATION_PERIODS_VALIDATION_ID = "config-declaration-periods-validation"
DECLARATION_PERIODS_LIST_MAX_SIZE = 10

NSIP_SYNC_SHOW_DIFF_ID = "nsip-sync-show-diff-button"
NSIP_SYNC_APPLY_DIFF_ID = "nsip-sync-apply-diff-button"
NSIP_SYNC_CONTENT_ID = "nsip-project-sync-content"
NSIP_SYNC_ACTIVITY_TYPE_ID = "nsip-sync-activity-type"
NSIP_SYNC_ACTIVITY_TYPE_PROJECT = 1
NSIP_SYNC_ACTIVITY_TYPE_OTHER = 2

PROJECT_MGT_MASTERPROJECT_LIST_ID = "project-mgt-masterproject-list"
PROJECT_MGT_PROJECT_LIST_ID = "project-mgt-project-list"
PROJECT_MGT_PROJECT_ACTIVITY_ID = "project-mgt-is-project"
PROJECT_MGT_PROJECT_TYPE_ID = "project-mgt-project-type"
PROJECT_MGT_ACTION_BUTTON_ID = "project-mgt-action-button"
PROJECT_MGT_ACTION_BUTTON_DISABLE = "Désactiver"
PROJECT_MGT_ACTION_BUTTON_ENABLE = "Réactiver"
PROJECT_MGT_STATUS_ID = "project-mgt-status"
PROJECT_MGT_PROJECT_TYPE_NSIP = 0
PROJECT_MGT_PROJECT_TYPE_LOCAL = 1
PROJECT_MGT_PROJECT_TYPE_DISABLED = 2
PROJECT_MGT_LIST_MAX_SIZE = 10
PROJECT_MGT_LIST_BOX_WIDTH = 5
PROJECT_MGT_LIST_BOX_WIDTH_XXL = 5

TABLE_NSIP_PROJECT_SYNC_ID = "nsip-project-sync"

PROJECT_CHANGE_ADDED = "Ajouté"
PROJECT_CHANGE_CHANGED = "Modifié"
PROJECT_CHANGE_REMOVED = "Supprimé"
