# Helper functions to manage the data cache

from ositah.utils.exceptions import SessionDataMissing
from ositah.utils.utils import GlobalParams, no_session_id_jumbotron


def clear_cached_data():
    """
    Clear the data cached by the previous requests

    :return: None
    """

    global_params = GlobalParams()
    try:
        session_data = global_params.session_data
        session_data.reset_caches()
    except SessionDataMissing:
        return no_session_id_jumbotron()
