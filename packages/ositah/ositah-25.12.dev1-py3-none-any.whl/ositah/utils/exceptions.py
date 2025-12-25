# OSITAH exceptions not specific to one of the sub-application

from hito_tools.exceptions import EXIT_STATUS_GENERAL_ERROR


class InvalidCallbackInput(Exception):
    def __init__(self, input_name):
        self.msg = f"internal error: invalid input ({input_name}) in callback"
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)


class InvalidDataSource(Exception):
    def __init__(self, source):
        self.msg = f"attempt to use and invalid data source ({source})"
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)


class InvalidHitoProjectName(Exception):
    def __init__(self, projects):
        self.msg = (
            f"The following Hito project names don't match the format 'masterproject / project' :"
            f" {', '.join(projects)}"
        )
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)


class SessionDataMissing(Exception):
    def __init__(self, session_id=None):
        if session_id:
            session_txt = f" (session={session_id})"
        else:
            session_txt = ""
        self.msg = f"Attempt to use non existing session data{session_txt}"
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)


class ValidationPeriodAmbiguous(Exception):
    def __init__(self, date):
        self.msg = f"Configuration error: several periods matching {date}"
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)


class ValidationPeriodMissing(Exception):
    def __init__(self, date):
        self.msg = f"No defined declaration period matching {date}"
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)
