from datetime import datetime
from string import ascii_lowercase, digits
from random import choice
from inspect import getframeinfo, currentframe, getfile
from collections import deque
from io import BytesIO
import pandas as pd
from .exception import *


class BytesQueueBuffer:
    def __init__(self):
        self.buffer = deque()
        self._size = 0

    def __len__(self):
        return self._size

    def put(self, data):
        self.buffer.append(data)
        self._size += len(data)

    def get(self, n):
        if n == 0:
            return b""
        elif not self.buffer:
            raise RuntimeError("buffer is empty")
        elif n < 0:
            raise ValueError("n should be > 0")

        fetched = 0
        ret = BytesIO()
        while fetched < n:
            remaining = n - fetched
            chunk = self.buffer.popleft()
            chunk_length = len(chunk)
            if remaining < chunk_length:
                left_chunk, right_chunk = chunk[:remaining], chunk[remaining:]
                ret.write(left_chunk)
                self.buffer.appendleft(right_chunk)
                self._size -= remaining
                break
            else:
                ret.write(chunk)
                self._size -= chunk_length
            fetched += chunk_length

            if not self.buffer:
                break

        return ret.getvalue()


class HttpConnectionInfo:
    def __init__(self, http_address, http_username=None, http_password=None, access_token=None, http_proxy=None,
                 https_proxy=None, trusted_certificate_file=None):
        if http_address is None:
            raise OneTickException("HTTP address must be specified.", ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        pos = http_address.find(':', 6)  # first ':' symbol after http or https prefixes
        if pos != -1:
            try:
                port = http_address[pos + 1:]
                if int(port) <= 0:
                    raise OneTickException(f"Port number must be positive, however http_address={http_address} was "
                                           f"specified", ErrorTypes.ERROR_INVALID_INPUT,
                                           getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
            except Exception:
                raise OneTickException(f"Port must be a positive number, however http_address={http_address} was "
                                       f"specified", ErrorTypes.ERROR_INVALID_INPUT,
                                       getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        if http_address.find('/omdwebapi/rest') == -1:
            self.url_ = http_address + "/omdwebapi/rest/"
        else:
            self.url_ = http_address
        self.http_username_ = http_username
        self.http_password_ = http_password
        self.access_token_ = access_token
        self.trusted_certificate_file_ = trusted_certificate_file
        self.proxies_ = {}
        if http_proxy:
            self.proxies_["http"] = http_proxy
        elif os.getenv("HTTP_PROXY"):
            self.proxies_["http"] = os.getenv("HTTP_PROXY")
        if https_proxy:
            self.proxies_["https"] = https_proxy
        elif os.getenv("HTTPS_PROXY"):
            self.proxies_["https"] = os.getenv("HTTPS_PROXY")


def get_local_timezone_name():
    localzone_name = None
    try:
        localzone_name = os.environ.get('TZ')
        if not localzone_name:
            from tzlocal import get_localzone_name
            localzone_name = get_localzone_name()
    except Exception as error:
        print("[ERROR] Unable to detect local timezone: {}".format(error))
    if not localzone_name:
        print("[ERROR] Unable to detect local timezone. Defaulting to GMT.")
        localzone_name = 'GMT'
    return localzone_name


def get_reference_counted_prefix():
    return '__OMD_INTERNAL_MARK__'


ref_count = {}


def inc_ref_count(key):
    if key in ref_count:
        ref_count[key] = ref_count[key] + 1
    else:
        ref_count[key] = 1


def dec_ref_count(key):
    if key in ref_count:
        ref_count[key] = ref_count[key] - 1
    else:
        raise OneTickException('reference count can not be negative for sting {}'.format(key), ErrorTypes.ERROR_GENERIC,
                               getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)


def get_ref_count(key):
    if str in ref_count:
        return ref_count[key]
    return 0


cached_memory_files = {}


def save_in_memory(file_name, content, last_modification_time):
    idx = file_name.find("::")
    if idx != -1:
        cached_memory_files[file_name[0:idx]] = (content, last_modification_time)
    cached_memory_files[file_name] = (content, last_modification_time)


def get_from_memory(file_name):
    return cached_memory_files[file_name]


def remove_from_memory(file_name):
    if file_name in cached_memory_files:
        del cached_memory_files[file_name]


def create_unique_file_name():
    return ''.join(choice(ascii_lowercase + digits) for _ in range(10)) + "_" + datetime.now().strftime('%Y%m%d%H%M%S')


def create_unique_query_file_name(query):
    root_file_name_line_num = ''
    if query is not None and query.root_ is not None:
        root_file_name_line_num = query.root_.stack_info.replace(":", "_")
        root_file_name_line_num = root_file_name_line_num.replace("/", "_")
        root_file_name_line_num = root_file_name_line_num.replace("\\", "_")
        root_file_name_line_num = root_file_name_line_num.replace(" ", "_")
    return "memory/" + root_file_name_line_num + get_reference_counted_prefix() + create_unique_file_name()


def str_to_datetime(str_obj):
    if len(str_obj) > 2 and str_obj[0:2] == "UT":
        data = str_obj[2:].split('.')
        if len(data) != 3 and len(data) != 4:
            raise OneTickException(f'Invalid time {str_obj} is specified', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        if len(data) == 3:
            return pd.to_datetime(1000 * int(data[0]) + int(data[1]), unit='ms')
        else:
            return pd.to_datetime(1000000000 * int(data[0]) + 1000 * int(data[1]) + int(data[2]) / 1000, unit='ns')

    str_format = "%Y%m%d%H%M%S"
    if '.' in str_obj:
        str_format = str_format + '.'
    str_format = str_format + "%f"
    return pd.to_datetime(str_obj, format=str_format)


def datetime_to_str(time_param):
    result = time_param

    if time_param and isinstance(time_param, str):
        if len(time_param) == 8:  # YYYYMMDD
            result += "000000"

    if time_param and isinstance(time_param, pd.Timestamp):
        time_format = '%Y%m%d%H%M%S.%f'
        result = time_param.strftime(time_format)
        if time_param.nanosecond:
            result = result + str(time_param.nanosecond).zfill(3)

    elif time_param and isinstance(time_param, datetime):
        time_format = '%Y%m%d%H%M%S.%f' if time_param.microsecond else '%Y%m%d%H%M%S'
        result = time_param.strftime(time_format)

    return result


def date_to_str(date_param):
    result = date_param

    if date_param and isinstance(date_param, str):
        if len(date_param) > 8:
            result = date_param[0:8]  # YYYYMMDD

    if date_param and (isinstance(date_param, pd.Timestamp) or isinstance(date_param, datetime)):
        result = date_param.strftime('%Y%m%d')

    return result


def make_register_decorator():
    registered_functions = {}

    def _convert_file_path_to_dict_entry(file_name):
        file_name = file_name.replace('\\', '/')
        if file_name[-1] == 'c':  # if extension is .pyc
            return file_name[:-1]
        return file_name

    def _make_no_args_decorator(name):
        def decorator(func):
            file_name = getfile(func)
            file_name = _convert_file_path_to_dict_entry(file_name)
            if not (file_name in registered_functions):
                registered_functions[file_name] = []
            registered_functions[file_name].append((name, func))
            return func

        return decorator

    def _decorator_with_arg(arg):
        if isinstance(arg, str):
            return _make_no_args_decorator(arg)
        else:
            return _make_no_args_decorator(arg.__name__)(arg)

    _decorator_with_arg._registered_functions = registered_functions
    return _decorator_with_arg


valid_query_properties = {
    "ONE_TO_MANY_SYMBOL_MAPPING_POLICY",
    "ALLOW_GRAPH_REUSE",
    "USER_DEFINED_PROPERTIES",
    "DB_HINT_FOR_PROCESSING_HOST",
    "QUERY_SENT_WITHOUT_PREPROCESSING_FLAG",
    "USE_SAME_CONNECTION_FOR_REMOTE_HOST",
    "DBS_FOR_FEEDBACK_QUEUES",
    "SYMBOL_PARAM_FOR_DISPATCH_THREAD",
    "RESOURCE_LIMITS",
    "DISABLE_INITIALIZATION_QUERY_FLAG",
    "PARALLEL_CONNECTION_ID_FOR_SERVER_REQUESTS",
    "CLIENT_VERSION_FOR_SERVER_REQUESTS",
    "CLIENT_BYTE_ORDER_FOR_SERVER_REQUESTS",
    "TREAT_LOCAL_DB_AS_SERVER_SIDE_FLAG",
    "SKIP_CEP_STITCHING",
    "ADD_MEASURE_PERF_EPS",
    "PARAMS_CONVERTED_TO_SYMBOL_PARAMS_FLAG",
    "ENCRYPTED_OTQ",
    "REMOTE_NAMED_QUEUES",
    "CONTINOUES_REMOTE_NAMED_QUEUES_FLAG",
    "CEP_NUM_DISPATCH_THREADS",
    "CEP_KEEP_ORIGINAL_TIMESTAMP",
    "DBS_FOR_EXTERNAL_QUEUES",
    "TREAT_CONNECT_ERROR_AS_SYMBOL_ERROR",
    "OPTIMIZE_QUERY",
    "REF_DATA_OTQ_QUERY",
    "REF_DATA_OTQ_QUERY_PARAMS",
    "FLUSH_USER_REF_DATA_CACHE",
    "SUPPORT_REF_DATA_RELOAD_IN_CEP",
    "SKIP_AUTHENTICATION",
    "USERNAME_FOR_AUTHENTICATION",
    "CEP_CHECK_SYMBOL_HISTORY_UPDATES",
    "ENABLE_TICK_BLOCK_SUPPORT",
    "END_CLIENT_HOSTNAME",
    "CEP_OUTPUT_LATENCY_MODE",
    "IGNORE_REALTIME_DB",
    "IGNORE_TICKS_IN_UNENTITLED_TIME_RANGE",
    "CEP_USE_CROSS_MOUNT_PRESORT_FOR_RAW_HRTBT",
    "CLUSTER_ID_TO_USE",
    "IGNORE_DB_SYMBOLOGY",
    "CLIENT_SIDE_CONCURRENCY",
    "USE_SYMBOLS_FROM_CEP_ADAPTER",
    "PROCESS_APPLY_TIMES_DAILY_CONCURRENTLY",
    "KEEP_TIME_ORDER_FOR_CONCURRENT_APPLY_TIMES_DAILY",
    "BATCH_SIZE_FOR_LOAD_BALANCING",
    "CEP_DO_NOT_SUBMIT_SAFE_HEARTBEAT",
    "USE_FT",
    "FT_PROPERTIES",
    "SEND_HIDDEN_TICKS",
    "ALLOW_OTQ_AS_EP_BINDINGS_TO_BE_IGNORED",
    "SEND_CALLBACKS_FOR_RARE_HIGH_LEVEL_USE",
    "USE_REALTIME_OUTPUT_MODE",
    "REQUIRE_GRAPH_REUSE",
    "SEND_POSITION_IN_SERVER_QUEUE",
    "NESTED_OTQS_USE_ONLY_SINKS_FOR_OUTPUT",
    "HIGH_PRIORITY_QUERY",
    "PREPEND_QUERY_NAME_TO_SCOPE_ID",
    "APPLY_DEFAULT_DB_SCHEMA",
    "BATCH_SIZE",
    "MAX_CONCURRENCY",
    "APPLY_TIMES_DAILY",
    "PROCESS_DBS_CONCURRENTLY",
    "REPLACE_EPS_WITH_SIDE_EFFECTS",
    "REPORT_TS_RESOURCE_USAGE",
    "POST_FILTER",
    "INTERNAL_QUERY",
    "CLIENT_SIDE_BATCH_SIZE",
    "NUM_INPUT_TICKS_BTW_HEARTBEATS_FOR_MERGED_TS",
    "CLIENT_SIDE_VDBS_TO_SEND"
}
