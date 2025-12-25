# Exceptions for applications based on this module

from datetime import datetime

# Status code in case of errors
EXIT_STATUS_CONFIG_ERROR = 1
EXIT_STATUS_INVALID_SQL_VALUE = 20
EXIT_STATUS_GENERAL_ERROR = 30


class ConfigFileEmpty(Exception):
    def __init__(self, file):
        self.msg = f"No configuration parameter defined in {file}"
        self.status = EXIT_STATUS_CONFIG_ERROR

    def __str__(self):
        return repr(self.msg)


class ConfigInvalidParamValue(Exception):
    def __init__(self, param, value, file=None):
        if file:
            file_msg = " (file={file})"
        self.msg = f"Invalid configuration parameter value ({value}) for '{param}'{file_msg}"
        self.status = EXIT_STATUS_CONFIG_ERROR

    def __str__(self):
        return repr(self.msg)


class ConfigMissingParam(Exception):
    def __init__(self, param, file=None):
        if file:
            file_msg = " (file={file})"
        else:
            file_msg = ""
        self.msg = f"Missing required configuration parameter '{param}'{file_msg}"
        self.status = EXIT_STATUS_CONFIG_ERROR

    def __str__(self):
        return repr(self.msg)


class OptionMissing(Exception):
    def __init__(self, option):
        self.msg = f"Option '{option}' required but missing"
        self.status = EXIT_STATUS_CONFIG_ERROR

    def __str__(self):
        return repr(self.msg)


class NSIPPeriodAmbiguous(Exception):
    def __init__(self, date, num_matches):
        if date is None:
            date = datetime.now()
        self.msg = f"Several declaration periods ({num_matches}) found in NSIP matching {date}"
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)


class NSIPPeriodMissing(Exception):
    def __init__(self, date):
        self.msg = f"No declaration period found in NSIP matching {date}"
        self.status = EXIT_STATUS_GENERAL_ERROR

    def __str__(self):
        return repr(self.msg)


class SQLArrayMalformedValue(Exception):
    def __init__(self, longtext, value, index):
        self.msg = (
            f"SQL longtext array: malformed value ({value}) at index {index}"
            f" (longtext={longtext})"
        )
        self.status = EXIT_STATUS_INVALID_SQL_VALUE

    def __str__(self):
        return repr(self.msg)


class SQLInconsistentArrayLen(Exception):
    def __init__(self, longtext, expected_length, actual_length):
        self.msg = (
            f"SQL longtext array: expected length is {expected_length} but actual length"
            f" is {actual_length} (longtext={longtext})"
        )
        self.status = EXIT_STATUS_INVALID_SQL_VALUE

    def __str__(self):
        return repr(self.msg)


class SQLInvalidArray(Exception):
    def __init__(self, longtext):
        self.msg = f"Invalid SQL longtext array: {longtext}"
        self.status = EXIT_STATUS_INVALID_SQL_VALUE

    def __str__(self):
        return repr(self.msg)
