import os


class ErrorTypes:
    ERROR_INVALID_ARGUMENT = "ERROR_INVALID_ARGUMENT"
    ERROR_INVALID_API_USE = "ERROR_INVALID_API_USE"
    ERROR_INVALID_INPUT = "ERROR_INVALID_INPUT"
    ERROR_INVALID_GRAPH = "ERROR_INVALID_GRAPH"
    ERROR_GENERIC = "ERROR_GENERIC"
    ERROR_UNSUPPORTED = "ERROR_UNSUPPORTED"


class OneTickException(Exception):
    def __init__(self, msg, error_code=ErrorTypes.ERROR_GENERIC, file_name=None, file_line=None):
        error_msg = "{error_code}: {msg}".format(error_code=error_code, msg=msg)
        if os.getenv("PYTHON_TEST_FLAG") != "1" and file_name and file_line:
            error_msg = "{error_code}: {msg} {file_name}:{file_line}".format(
                error_code=error_code, msg=msg, file_name=file_name, file_line=file_line)
        super(Exception, self).__init__(error_msg)
