from ._internal_utils import *
from .exception import *
from inspect import getframeinfo, currentframe
import json as _json


class Configuration:
    class _Parsers:
        @staticmethod
        def invalid_parser(str_value):
            raise OneTickException(f"{str_value} cannot be parsed from config file",
                                   ErrorTypes.ERROR_INVALID_INPUT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)

        def parse_string(str_value):
            return str_value

        @staticmethod
        def parse_int(str_value):
            return int(str_value)

        @staticmethod
        def parse_datetime(str_value):
            return str_to_datetime(str_value)

        @staticmethod
        def parse_bool(str_value):
            if str_value.lower() in ['true', '1', 't', 'y', 'yes']:
                return True
            elif str_value.lower() in ['false', '0', 'f', 'n', 'no']:
                return False
            else:
                raise ValueError(f"Invalid boolean string: {str_value}")

        @staticmethod
        def parse_json(str_value):
            return _json.loads(str_value)

    def register_parameter(self, name, value, parser_function=None):
        self._parsers[name] = parser_function
        return value

    def __init__(self):
        self._parsers = {}

        self.http_address = self.register_parameter('http_address', None, Configuration._Parsers.parse_string)
        self.bs_ticks = self.register_parameter('bs_ticks', None, Configuration._Parsers.parse_int)
        self.bs_time_msec = self.register_parameter('bs_time_msec', None, Configuration._Parsers.parse_int)
        self.symbols = self.register_parameter('symbols', None, Configuration._Parsers.parse_json)
        self.username = self.register_parameter('username', None, Configuration._Parsers.parse_string)
        self.context = self.register_parameter('context', None, Configuration._Parsers.parse_string)
        self.timezone = self.register_parameter('timezone', None, Configuration._Parsers.parse_string)
        self.query_properties = self.register_parameter('query_properties', None, Configuration._Parsers.parse_json)
        self.symbol_date = self.register_parameter('symbol_date', None, Configuration._Parsers.parse_int)
        self.start = self.register_parameter('start', None, Configuration._Parsers.parse_datetime)
        self.end = self.register_parameter('end', None, Configuration._Parsers.parse_datetime)
        self.apply_times_daily = self.register_parameter('apply_times_daily', None, Configuration._Parsers.parse_bool)
        self.query_params = self.register_parameter('query_params', None, Configuration._Parsers.parse_json)
        self.max_concurrency = self.register_parameter('max_concurrency', None, Configuration._Parsers.parse_int)
        self.compression = self.register_parameter('compression', "zstd", Configuration._Parsers.parse_string)
        self.http_username = self.register_parameter('http_username', None, Configuration._Parsers.parse_string)
        self.http_password = self.register_parameter('http_password', None, Configuration._Parsers.parse_string)
        self.running_query_flag = self.register_parameter('running_query_flag', False,
                                                          Configuration._Parsers.parse_bool)
        self.query_name = self.register_parameter('query_name', None, Configuration._Parsers.parse_string)
        self.output_structure = self.register_parameter('output_structure', 'symbol_result_map',
                                                        Configuration._Parsers.parse_string)
        self.output_mode = self.register_parameter('output_mode', 'numpy', Configuration._Parsers.parse_string)
        self.encoding = self.register_parameter('encoding', 'utf-8', Configuration._Parsers.parse_string)
        self.treat_byte_arrays_as_strings = self.register_parameter('treat_byte_arrays_as_strings', True,
                                                                    Configuration._Parsers.parse_bool)
        self.callback = self.register_parameter('callback', None, Configuration._Parsers.invalid_parser)
        self.start_time_expression = self.register_parameter('start_time_expression', None,
                                                             Configuration._Parsers.parse_string)
        self.end_time_expression = self.register_parameter('end_time_expression', None,
                                                           Configuration._Parsers.parse_string)
        self.svg_path = self.register_parameter('svg_path', None, Configuration._Parsers.parse_string)
        self.access_token = self.register_parameter('access_token', None, Configuration._Parsers.parse_string)
        self.http_proxy = self.register_parameter('http_proxy', None, Configuration._Parsers.parse_string)
        self.https_proxy = self.register_parameter('https_proxy', None, Configuration._Parsers.parse_string)
        self.use_python_style_nulls_for_missing_values = self.register_parameter(
            'use_python_style_nulls_for_missing_values', False, Configuration._Parsers.parse_bool)
        self.trusted_certificate_file = self.register_parameter('trusted_certificate_file', None,
                                                                Configuration._Parsers.parse_string)

    def from_file(self, config_file_path):
        with open(config_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('=', 1)
                if len(parts) == 2:
                    name, str_value = parts
                    if name in self._parsers:

                        if self._parsers[name] is Configuration._Parsers.invalid_parser:
                            raise OneTickException(f"Parameter '{name}' cannot be passed from {config_file_path} config file",
                                                   ErrorTypes.ERROR_INVALID_INPUT,
                                                   getframeinfo(currentframe()).filename,
                                                   getframeinfo(currentframe()).lineno)

                        str_value = self._parsers[name](str_value)
                        setattr(self, name, str_value)
                    else:
                        raise OneTickException(f"Unknown parameter {name} in config file {config_file_path}",
                                               ErrorTypes.ERROR_INVALID_INPUT, getframeinfo(currentframe()).filename,
                                               getframeinfo(currentframe()).lineno)
                else:
                    raise OneTickException(f"Invalid line '{line}' in config file {config_file_path}",
                                           ErrorTypes.ERROR_INVALID_INPUT, getframeinfo(currentframe()).filename,
                                           getframeinfo(currentframe()).lineno)


config = Configuration()