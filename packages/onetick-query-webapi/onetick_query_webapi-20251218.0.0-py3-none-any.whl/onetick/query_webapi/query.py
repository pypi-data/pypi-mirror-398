import time
import json as _json

import requests as _requests
from datetime import datetime
import copy as _copy
from ._internal_utils import *
from .configuration import *
from . import config as _config
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
from . import graph_components as _graph_components
from . import ep as _ep
from collections import defaultdict, namedtuple
from . import _eps_factory
from .utils import *
from .exception import *
import base64
import uuid
from functools import reduce
from threading import Lock

# zstandard and gzip are not used directly but they are used by requests lib to decode response streams
# we include them to make sure that they are installed
import zstandard
import gzip

polars_imported = True
try:
    import polars as pl
except ImportError:
    polars_imported = False

open_id_imported = True
try:
    from . import open_id
except ImportError:
    open_id_imported = False


graphviz_imported = True
try:
    import tempfile as _tempfile
    import graphviz as _gv
except ImportError:
    graphviz_imported = False
    
    
_cookies_cache = {}


class QueryProperties:
    def __init__(self):
        self._properties = {}

    def get_properties(self):
        return self._properties

    def set_property_value(self, name: str, value: str):
        self._properties[name] = value

    def get_property_value(self, name):
        return self._properties.get(name)

    def set_user_defined_properties(self, value):
        USER_DEFINED_PROPERTIES = "USER_DEFINED_PROPERTIES"
        return self.set_property_value(USER_DEFINED_PROPERTIES, value)

    def get_user_defined_properties(self):
        USER_DEFINED_PROPERTIES = "USER_DEFINED_PROPERTIES"
        return self.get_property_value(USER_DEFINED_PROPERTIES)

    def convert_to_name_value_pairs_string(self):
        items = ','.join([f'{k}={quoted(v)}' for k, v in self._properties.items()])
        return items


class OneTickJsonEncoder(_json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Symbol):
            if obj.params:
                return obj.name, obj.params
            else:
                return obj.name, dict()
        if isinstance(obj, np.datetime64) or isinstance(obj, pd.Timestamp) or isinstance(obj, datetime):
            return str(obj)
        return _json.JSONEncoder.default(self, obj)


class QueryCancellationHandle:

    def __init__(self):
        self._lock = Lock()
        self._cancellation_id = None
        self._http_info = None
        self._auth = None
        self._headers = None
        self._cancellation_requested = False
        self._cookies = None

    def _initialize(self, http_info: HttpConnectionInfo, auth, headers, cancellation_id, cookies):
        with self._lock:
            self._http_info = http_info
            self._auth = auth
            self._headers = headers
            self._cancellation_id = cancellation_id
            self._cancel_query_if()
            self._cookies = cookies

    def _send_cancellation_request(self):
        request_params = {'query_type': "cancel", 'cancellation_handle': str(self._cancellation_id), }
        json_params_str = _json.dumps(request_params)

        verify = True if self._http_info.trusted_certificate_file_ is None else self._http_info.trusted_certificate_file_
        res = _requests.post(self._http_info.url_, auth=self._auth, headers=self._headers, cookies=self._cookies,
                             data=json_params_str, proxies=self._http_info.proxies_, verify=verify)
        if not res.ok:
            print('Unable to cancel query: ' + str(res.content, 'utf-8'))
        else:
            print('Query is cancelled successfully: ' + str(res.content, 'utf-8'))

    def _cancel_query_if(self):
        if self._http_info is None:
            return
        if self._cancellation_id is None:
            return
        if self._cancellation_requested is False:
            return
        self._send_cancellation_request()

    def cancel_query(self):
        with self._lock:
            if self._cancellation_requested:
                raise OneTickException('cancel_query should be called only once', ErrorTypes.ERROR_GENERIC,
                                       getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
            self._cancellation_requested = True
            self._cancel_query_if()


class OutputStructure:
    symbol_result_map = 'symbol_result_map'
    symbol_result_list = 'symbol_result_list'
    result_map = 'result_map'

class QueryOutputMode:
    callback = 'callback'
    numpy = 'numpy'
    pandas = 'pandas'
    pyarrow = 'pyarrow'
    polars = 'polars'


class CallbackBase:
    def __init__(self):
        """
        Method ``__init__()`` can be used for callback initialization.
        Can be used to define some variables for future use
        in callback methods.
        """
        pass

    def replicate(self):
        """
        Called to replicate the callback object for each output node.
        May also be used for internal copying of callback object.

        Returns
        -------
            By default reference to this callback object
        """
        return self

    def process_symbol_name(self, symbol_name):
        """
        Invoked to supply the name of the security that produces
        all the ticks that will be delivered to this callback object.
        If these ticks are provided by several securities,
        the ``symbol_name`` parameter is set to empty string.

        Parameters
        ----------
        symbol_name: str
            name of security

        """
        pass

    def process_callback_label(self, callback_label):
        """
        Called immediately before :meth:`process_symbol_name`
        to supply label assigned to callback.

        Parameters
        ----------
        callback_label: str
            label assigned to this callback object
        """
        pass

    def process_symbol_parameters(self, symbol_params):
        pass

    def process_data_quality_change(self, symbol_name, data_quality, time):
        """
        Called to report a data quality change, such as collection outage.

        Parameters
        ----------
        symbol_name: str
            Symbol name for each data quality change is propagated.
        data_quality: int
            parameter has the following meaning:

            * `QUALITY_UNKNOWN` = -1,
            * `QUALITY_OK`,
            * `QUALITY_STALE` = 1,
            * `QUALITY_MISSING` = 2,
            * `QUALITY_PATCHED` = 4,
            * `QUALITY_MOUNT_BAD` = 9,
            * `QUALITY_DISCONNECT` = 17,
            * `QUALITY_COLLECTOR_FAILURE` = 33,
            * `QUALITY_DELAY_STITCHING_WITH_RT` = 64,
            * `QUALITY_OK_STITCHING_WITH_RT` = 66
        time: datetime
            Time of the change in GMT timezone.
        """
        pass

    def process_error(self, error_code, error_msg):
        """
        Called to report a per-security error or per-security warning.

        error_code: int
            Values of error code less than 1000 are warnings.
            Warnings signal issues which might not affect results of the query
            and thus could be chosen to be ignored
        error_msg: str
            Error message
        """
        pass

    def process_ticks(self, ticks):
        """
        Called to deliver each tick.

        Parameters
        ----------
        ticks: dict
            mapping of field names to field values

        """
        pass

    def done(self):
        """
        Invoked when all the raw or computed ticks for a given request
        were submitted to the callback using the :meth:`process_tick` method.

        """
        pass


class _ArrowParserCallbackForHistoricalQuery(CallbackBase):
    def __init__(self):
        super().__init__()
        self.symbol_name = ""
        self.callback_label = ""
        self.symbol_params = {}
        self.chunks_of_ticks = []
        self.chunks_of_data_quality_changes = []
        self.chunks_of_errors = []

    def replicate(self):
        return _ArrowParserCallbackForHistoricalQuery()

    def process_symbol_name(self, symbol_name):
        self.symbol_name = symbol_name

    def process_callback_label(self, callback_label):
        self.callback_label = callback_label

    def process_symbol_parameters(self, symbol_params):
        self.symbol_params = symbol_params

    def process_data_quality_change(self, symbol_name, data_quality, time):
        self.chunks_of_data_quality_changes.append((symbol_name, data_quality, time))

    def process_error(self, error_code, error_msg):
        self.chunks_of_errors.append((error_code, error_msg))

    def process_ticks(self, ticks):
        self.chunks_of_ticks.append(ticks)

    def done(self):
        pass


class ArrowParser:
    def __init__(self, verbose=False, treat_byte_arrays_as_strings=True, encoding='utf-8', callback=None,
                 use_python_style_nulls_for_missing_values=None):

        self.callback_mode = callback is not None

        self._encoding = encoding
        self._treat_byte_arrays_as_strings = treat_byte_arrays_as_strings
        self._use_python_style_nulls_for_missing_values = use_python_style_nulls_for_missing_values

        if callback is None:
            self._callback = _ArrowParserCallbackForHistoricalQuery()
        else:
            self._callback = callback

        self._callbacks = {}
        self.verbose = verbose

    def callback_exists(self, callback_id):
        return callback_id in self._callbacks

    def get_callback(self, callback_id):
        if callback_id not in self._callbacks:
            self._callbacks[callback_id] = self._callback.replicate()
        return self._callbacks[callback_id]

    @staticmethod
    def _convert_time_fields_to_timestamps(table):
        for i, field in enumerate(table.schema):
            if field.name == 'Time':
                table = table.remove_column(i)
                continue
            if field.metadata is not None and field.metadata.get(b'TIMESTAMP_TYPE') is not None:
                column = table.column(i)
                table = table.remove_column(i)
                table = table.add_column(i, 'Time' if field.name == 'TIMESTAMP' else field.name, column.cast(
                    pa.timestamp('ns' if field.metadata.get(b'TIMESTAMP_TYPE') == b'NANO' else 'ms', tz='GMT')))
        return table

    def process_chunk(self, uncompressed_content, http_info: HttpConnectionInfo = None, auth=None, headers=None,
                      request_id=None, cookies=None):
        content_size = len(uncompressed_content)
        offset = 0

        while offset < content_size:
            buffer_reader = pa.BufferReader(uncompressed_content)
            buffer_reader.seek(offset)
            reader = pa.ipc.RecordBatchStreamReader(buffer_reader)

            table = reader.read_all()
            msg_type = table.schema.metadata[b'MSG_TYPE']

            if msg_type == b'PROCESS_DATA_QUALITY_CHANGE':
                callback_id = table.column("CALLBACK_ID")[0]
                data_quality_type = table.column("DATA_QUALITY_TYPE")[0]
                symbol_name = table.column("SYMBOL_NAME")[0]
                timestamp = table.column("TIMESTAMP")[0]
                callback = self.get_callback(callback_id)
                callback.process_data_quality_change(str(symbol_name),
                                                     data_quality_type,
                                                     np.datetime64(timestamp.as_py(), 'ns', ))

            elif msg_type == b'EXCEPTION':
                raise OneTickException(str(table.column("EXCEPTION_MSG")[0]), ErrorTypes.ERROR_GENERIC,
                                       getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

            elif msg_type == b'ERROR':
                error_code = table.column("SYMBOL_ERROR_CODE")[0].as_py()
                error_msg = table.column("SYMBOL_ERROR_MSG")[0].as_py()

                if error_code == 1021:
                    if _config.API_CONFIG['ENABLE_DEBUG_LOGS'] == 1:
                        print(f"Received upload {error_msg} file request")
                    file_path = error_msg
                    if file_path in cached_memory_files:
                        content, last_modification_time = get_from_memory(file_path)
                    else:
                        if file_path.startswith("remote://"):
                            content, query_name = GraphQuery.download_remote_file(file_path, http_info=http_info)
                            last_modification_time = 1000 * time.time()
                        else:
                            with open(file_path, encoding="utf-8") as f:
                                content = f.read()
                                last_modification_time = 1000 * os.path.getmtime(file_path)
                    base64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                    request_params = {'query_type': "upload_file",
                                      'request_id': request_id,
                                      'upload_file_name': file_path,
                                      'upload_file_content': base64_content,
                                      'last_modification_time': str(last_modification_time),
                                      'response': "arrow"}

                    json_params_str = _json.dumps(request_params, ensure_ascii=False, cls=OneTickJsonEncoder)
                    verify = True if http_info.trusted_certificate_file_ is None else http_info.trusted_certificate_file_
                    res = _requests.post(http_info.url_, auth=auth, data=json_params_str, headers=headers,
                                         proxies=http_info.proxies_, verify=verify, cookies=cookies)
                    if not res.ok:
                        raise OneTickException("Unable to upload file" + str(res.content, 'utf-8'),
                                               ErrorTypes.ERROR_GENERIC, getframeinfo(currentframe()).filename,
                                               getframeinfo(currentframe()).lineno)
                    if _config.API_CONFIG['ENABLE_DEBUG_LOGS'] == 1:
                        print(f"Upload cookies = {cookies}")
                        print("Sent requested content")
                else:
                    callback_id = table.column("CALLBACK_ID")[0]

                    is_query_level_callback = not self.callback_exists(callback_id)
                    callback = self.get_callback(callback_id)
                    if is_query_level_callback:
                        callback.process_symbol_name('QUERY_LEVEL_MSGS')
                    callback.process_error(int(error_code), str(error_msg))

            elif msg_type == b'PROCESS_SYMBOL_PARAMETERS':
                callback_id = table.column("CALLBACK_ID")[0]
                callback = self.get_callback(callback_id)
                symbol_params = {}
                for name, value in zip(table.column("PARAMETER_NAMES")[0], table.column("PARAMETER_VALUES")[0]):
                    symbol_params[name.as_py()] = value.as_py()
                callback.process_symbol_parameters(symbol_params)

            elif msg_type == b'PROCESS_SYMBOL_NAME':
                callback_id = table.column("CALLBACK_ID")[0]
                symbol_name = table.column("SYMBOL_NAME")[0]
                callback_label = table.column("CALLBACK_LABEL")[0]

                callback = self.get_callback(callback_id)
                callback.process_symbol_name(str(symbol_name))
                callback.process_callback_label(str(callback_label))

            elif msg_type == b'PROCESS_EVENT':
                for callback_id in table.column("CALLBACK_ID").unique():
                    filter_expression = pc.field("CALLBACK_ID") == callback_id
                    filtered_table = table.filter(filter_expression).drop_columns("CALLBACK_ID")

                    filtered_table = ArrowParser._convert_time_fields_to_timestamps(filtered_table)

                    callback = self.get_callback(callback_id)
                    if not self.callback_mode:
                        callback.process_ticks(filtered_table)
                    else:
                        callback.process_ticks(
                            ArrowParser._convert_table_to_map_of_fields(filtered_table,
                                                                        self._treat_byte_arrays_as_strings,
                                                                        self._encoding,
                                                                        self._use_python_style_nulls_for_missing_values))
            else:
                print("unsupported event")
            offset = buffer_reader.tell()

    @staticmethod
    def _merge_tables(list_of_tables, use_python_style_nulls_for_missing_values):
        result_table = pa.concat_tables(list_of_tables, promote_options=u'permissive')

        return result_table

    @staticmethod
    def numpy_array_from_arrow_array(arrow_array):
        arrow_type = arrow_array.type
        buffers = arrow_array.buffers()
        assert len(buffers) == 2
        bitmap_buffer = buffers[0]
        data_buffer = buffers[1]
        if isinstance(arrow_type, type(pa.binary(1))):  # todo, is there a better way to typecheck?
            # mimics python/pyarrow/array.pxi::Array::to_numpy
            buffers = arrow_array.buffers()
            assert len(buffers) == 2
            dtype = "S" + str(arrow_type.byte_width)
            # arrow seems to do padding, check if it is all ok
            expected_length = arrow_type.byte_width * len(arrow_array)
            actual_length = len(buffers[-1])
            if actual_length < expected_length:
                raise ValueError('buffer is smaller (%d) than expected (%d)' % (actual_length, expected_length))
            array = np.frombuffer(buffers[-1], dtype,
                                  len(arrow_array))  # TODO: deal with offset ? [arrow_array.offset:arrow_array.offset + len(arrow_array)]
        else:
            dtype = arrow_array.type.to_pandas_dtype()
        array = np.frombuffer(data_buffer, dtype, len(arrow_array))
        if bitmap_buffer is not None:
            # arrow uses a bitmap https://github.com/apache/arrow/blob/master/format/Layout.md
            bitmap = np.frombuffer(bitmap_buffer, np.uint8, len(bitmap_buffer))
            # we do have to change the ordering of the bits
            mask = 1 - np.unpackbits(bitmap).reshape((len(bitmap), 8))[:, ::-1].reshape(-1)[:len(arrow_array)]
            array = np.ma.MaskedArray(array, mask=mask)
        return array

    @staticmethod
    def _convert_arrow_column_to_numpy_array(column, metadata, treat_byte_arrays_as_strings, encoding,
                                             use_python_style_nulls_for_missing_values):

        if pa.types.is_string(column.type):
            column = column.fill_null("")
        elif pa.types.is_fixed_size_binary(column.type):
            column = column.fill_null(bytearray(column.type.byte_width))
        elif pa.types.is_binary(column.type):
            column = column.fill_null(bytearray(0))
        elif not use_python_style_nulls_for_missing_values:
            column = column.fill_null(0)

        if treat_byte_arrays_as_strings and pa.types.is_fixed_size_binary(column.type):
            if metadata and b"DATA_TYPE" in metadata:
                dtype = str(metadata[b"DATA_TYPE"], "UTF8")
                arr = ArrowParser.numpy_array_from_arrow_array(column.combine_chunks())
                return arr.view(dtype)
            else:
                return np.asarray([val.decode(encoding) if val else "" for val in column.to_numpy()], dtype='U')

        if treat_byte_arrays_as_strings and pa.types.is_binary(column.type):
            return np.asarray([val.decode(encoding) if val else "" for val in column.to_numpy()], dtype='U')

        if pa.types.is_string(column.type):
            return column.to_numpy()

        return column.to_numpy()

    @staticmethod
    def _convert_table_to_list_of_fields(result_table, treat_byte_arrays_as_strings, encoding, use_python_style_nulls_for_missing_values):
        o_list_of_fields = []
        for i, field in enumerate(result_table.schema):
            column_name = field.name
            column = result_table.column(column_name)
            metadata = field.metadata
            o_list_of_fields.append(tuple((
                column_name,
                ArrowParser._convert_arrow_column_to_numpy_array(column, metadata, treat_byte_arrays_as_strings, encoding,
                                                                 use_python_style_nulls_for_missing_values)
            )))
        return o_list_of_fields

    @staticmethod
    def _convert_table_to_pandas_dataframe(result_table, treat_byte_arrays_as_strings, encoding, use_python_style_nulls_for_missing_values):
        # return result_table.to_pandas()
        data = ArrowParser._convert_table_to_list_of_fields(result_table, treat_byte_arrays_as_strings, encoding,
                                                            use_python_style_nulls_for_missing_values)
        return pd.DataFrame({col_name: col_value for col_name, col_value in data})

    @staticmethod
    def _convert_table_to_pyarrow_table(result_table, treat_byte_arrays_as_strings, encoding, use_python_style_nulls_for_missing_values):
        return result_table

    @staticmethod
    def _convert_table_to_polars_table(result_table, treat_byte_arrays_as_strings, encoding, use_python_style_nulls_for_missing_values):
        if polars_imported:
            data = pl.from_arrow(result_table)
            return data
        else:
            raise OneTickException("In order to use polars output please pip install polars library and make sure that its version is >=1.9",
                                   ErrorTypes.ERROR_GENERIC, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

    def get_result_as_list(self, table_converter):
        start_time = time.time()

        result = []
        global_total_ticks = 0

        for callback_id, callback in self._callbacks.items():

            s_symbol_name = str(callback.symbol_name)
            s_label = str(callback.callback_label)
            o_symbol_params = callback.symbol_params
            o_list_of_errors = callback.chunks_of_errors
            o_list_of_fields = []

            total_ticks = 0
            if len(callback.chunks_of_ticks) > 0:
                result_table = ArrowParser._merge_tables(callback.chunks_of_ticks, self._use_python_style_nulls_for_missing_values)
                o_list_of_fields = table_converter(result_table,
                                                   self._treat_byte_arrays_as_strings,
                                                   self._encoding,
                                                   self._use_python_style_nulls_for_missing_values)
                total_ticks = result_table.shape[0]

            result_object = (s_symbol_name, o_list_of_fields, o_list_of_errors, s_label, o_symbol_params)
            result.append(result_object)

            global_total_ticks = global_total_ticks + total_ticks

            if self.verbose:
                print("symbol:[%s], output:[%s], ticks:[%d]" % (s_symbol_name, s_label, total_ticks))

        if self.verbose:
            print("finished in %s seconds, processed %d ticks" % (time.time() - start_time, global_total_ticks))
        return result

    @staticmethod
    def _convert_table_to_map_of_fields(result_table, treat_byte_arrays_as_strings, encoding,
                                        use_python_style_nulls_for_missing_values):
        o_map_of_fields = {}

        for i, field in enumerate(result_table.schema):
            column_name = field.name
            column = result_table.column(column_name)
            metadata = field.metadata

            o_map_of_fields[column_name] = \
                ArrowParser._convert_arrow_column_to_numpy_array(column, metadata, treat_byte_arrays_as_strings,
                                                                 encoding, use_python_style_nulls_for_missing_values)
        return o_map_of_fields

    def get_result_as_output_label_map(self, table_converter):
        result = {}
        for callback_id, callback in self._callbacks.items():
            s_symbol_name = callback.symbol_name
            s_label = callback.callback_label

            o_list_of_errors = [(s_symbol_name, error_code, error_message) for error_code, error_message in
                                callback.chunks_of_errors]
            o_map_of_fields = pa.table([])

            if len(callback.chunks_of_ticks) > 0:
                result_table = ArrowParser._merge_tables(callback.chunks_of_ticks, self._use_python_style_nulls_for_missing_values)
                if not any("SYMBOL_NAME" == name.upper() for name in result_table.schema.names):
                    result_table = result_table.append_column("SYMBOL_NAME", pa.array([s_symbol_name] * len(result_table)))
                o_map_of_fields = result_table

            if s_label not in result:
                result[s_label] = {}
            if s_symbol_name not in result[s_label]:
                result[s_label][s_symbol_name] = (o_map_of_fields, o_list_of_errors)
            else:
                raise OneTickException("Multiple outputs for the same symbol and node name are produced."
                                       "Try using list as output structure or specify different output labels",
                                       ErrorTypes.ERROR_GENERIC, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

        final_result = {}

        for output_label, per_symbol_name_dictionary in result.items():

            per_output_label_data = reduce(
                lambda t1, t2: (
                    ArrowParser._merge_tables(
                        [t1[0], t2[0]],
                        self._use_python_style_nulls_for_missing_values
                    ),
                    t1[1]+t2[1]
                ),
                per_symbol_name_dictionary.values()
            )

            final_result[output_label] = (
                table_converter(per_output_label_data[0],
                                self._treat_byte_arrays_as_strings,
                                self._encoding,
                                self._use_python_style_nulls_for_missing_values),
                per_output_label_data[1]
            )



        return final_result

    def get_result_as_map(self, table_converter):
        start_time = time.time()
        global_total_ticks = 0

        result = {}
        for callback_id, callback in self._callbacks.items():
            s_symbol_name = callback.symbol_name
            s_label = callback.callback_label
            o_list_of_errors = callback.chunks_of_errors
            o_map_of_fields = {}

            total_ticks = 0

            if len(callback.chunks_of_ticks) > 0:
                result_table = ArrowParser._merge_tables(callback.chunks_of_ticks, self._use_python_style_nulls_for_missing_values)
                o_map_of_fields = table_converter(result_table,
                                                  self._treat_byte_arrays_as_strings,
                                                  self._encoding,
                                                  self._use_python_style_nulls_for_missing_values)
                total_ticks = result_table.shape[0]

            if s_symbol_name not in result:
                result[s_symbol_name] = {}
            if s_label not in result[s_symbol_name]:
                result[s_symbol_name][s_label] = (o_map_of_fields, o_list_of_errors)
            else:
                raise OneTickException("Multiple outputs for the same symbol and node name are produced. Try using list as output structure",
                                       ErrorTypes.ERROR_GENERIC, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

            global_total_ticks = global_total_ticks + total_ticks
            if self.verbose:
                print("symbol:[%s], output:[%s], ticks:[%d]" % (s_symbol_name, s_label, total_ticks))

        if self.verbose:
            print("finished in %s seconds, processed %d ticks" % (time.time() - start_time, global_total_ticks))
        return result

    def get_result(self, output_structure, output_mode):
        if (output_mode == QueryOutputMode.numpy):
            if output_structure == OutputStructure.symbol_result_map:
                return SymbolResultMap(self.get_result_as_map(ArrowParser._convert_table_to_map_of_fields))
            if output_structure == OutputStructure.symbol_result_list:
                return SymbolResultList(self.get_result_as_list(ArrowParser._convert_table_to_list_of_fields))
            if output_structure == OutputStructure.result_map:
                return ResultMap(self.get_result_as_output_label_map(ArrowParser._convert_table_to_map_of_fields))
        elif output_mode == QueryOutputMode.pandas:
            if output_structure == OutputStructure.symbol_result_map:
                return SymbolResultMap(self.get_result_as_map(ArrowParser._convert_table_to_pandas_dataframe))
            if output_structure == OutputStructure.symbol_result_list:
                return SymbolResultList(self.get_result_as_list(ArrowParser._convert_table_to_pandas_dataframe))
            if output_structure == OutputStructure.result_map:
                return ResultMap(self.get_result_as_output_label_map(ArrowParser._convert_table_to_pandas_dataframe))
        elif output_mode == QueryOutputMode.pyarrow:
            if output_structure == OutputStructure.symbol_result_map:
                return SymbolResultMap(self.get_result_as_map(ArrowParser._convert_table_to_pyarrow_table))
            if output_structure == OutputStructure.symbol_result_list:
                return SymbolResultList(self.get_result_as_list(ArrowParser._convert_table_to_pyarrow_table))
            if output_structure == OutputStructure.result_map:
                return ResultMap(self.get_result_as_output_label_map(ArrowParser._convert_table_to_pyarrow_table))
        elif output_mode == QueryOutputMode.polars:
            if output_structure == OutputStructure.symbol_result_map:
                return SymbolResultMap(self.get_result_as_map(ArrowParser._convert_table_to_polars_table))
            if output_structure == OutputStructure.symbol_result_list:
                return SymbolResultList(self.get_result_as_list(ArrowParser._convert_table_to_polars_table))
            if output_structure == OutputStructure.result_map:
                return ResultMap(self.get_result_as_output_label_map(ArrowParser._convert_table_to_polars_table))

        raise OneTickException('Unsupported output mode / output structure combination', ErrorTypes.ERROR_UNSUPPORTED,
                               getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

    def done(self):
        for callback_id, callback in self._callbacks.items():
            callback.done()


class ComputeFields(object):
    def __init__(self, mp):
        self.data_list = mp

    def __iter__(self):
        return (x for x in self.data_list if x is not None)

    def __len__(self):
        return len([x for x in self])

    def __repr__(self):
        return_string = ""
        for key in self.data_list:
            converted = repr(self.data_list[key]).strip()
            if return_string:
                return_string += ", "
            return_string += converted + " " + key

        return "\"" + return_string + "\""

    def __str__(self):
        return repr(self)


class QueryCommonProperties(object):
    """
    QueryCommonProperties class
    """

    def __init__(self):
        self.symbols_ = []
        self._start_time = None
        self._end_time = None
        self._start_time_expression = None
        self._end_time_expression = None
        self._timezone = None
        self._apply_time_daily = None
        self._symbol_date = 0
        self._query_properties = None  # name to value map
        self._query_params = None
        self._keep_otq_params_unresolved_flag = False
        self._running_query_flag = None
        self._callback = None
        self._empty_valid_params = []
        self._http_address = None
        self._http_username = None
        self._http_password = None
        self._access_token = None
        self._trusted_certificate_file = None
        self._max_concurrency = None

    def init(self, props):
        self.set_empty_valid_params(props.empty_valid_params())
        self.set_callback(props.callback())
        self.set_start_time(props.start_time())
        self.set_end_time(props.end_time())
        self.set_start_time_expression(props.start_time_expression())
        self.set_end_time_expression(props.end_time_expression())
        self.set_timezone(props.timezone())
        self.set_apply_times_daily(props.apply_times_daily())
        self.set_running_query_flag(props.running_query_flag())
        self.set_query_properties(props.query_properties())
        self.set_query_params(props.query_params())
        self.set_symbol_date(props.symbol_date())
        self.set_symbols(props.symbols())
        self.set_max_concurrency(props.max_concurrency())

    def set_empty_valid_params(self, empty_valid_params):
        self._empty_valid_params = empty_valid_params
        return self

    def empty_valid_params(self, empty_valid_params=None):
        if empty_valid_params is not None:
            return self.set_empty_valid_params(empty_valid_params)
        else:
            return self._empty_valid_params

    def set_callback(self, callback):
        self._callback = callback
        return self

    def callback(self, callback=None):
        if callback is not None:
            return self.set_callback(callback)
        else:
            return self._callback

    def set_start_time(self, start_time):
        self._start_time = start_time
        return self

    def start_time(self, start_time=None):
        if start_time is not None:
            return self.set_start_time(start_time)
        else:
            return self._start_time

    def set_end_time(self, end_time):
        self._end_time = end_time
        return self

    def end_time(self, end_time=None):
        if end_time is not None:
            return self.set_end_time(end_time)
        else:
            return self._end_time

    def set_timezone(self, timezone):
        self._timezone = timezone
        return self

    def set_start_time_expression(self, start_time_expression):
        self._start_time_expression = start_time_expression
        return self

    def start_time_expression(self, start_time_expression=None):
        if start_time_expression is not None:
            return self.set_start_time_expression(start_time_expression)
        else:
            return self._start_time_expression

    def set_end_time_expression(self, end_time_expression):
        self._end_time_expression = end_time_expression
        return self

    def end_time_expression(self, end_time_expression=None):
        if end_time_expression is not None:
            return self.set_end_time_expression(end_time_expression)
        else:
            return self._end_time_expression

    def timezone(self, timezone=None):
        if timezone is not None:
            return self.set_timezone(timezone)
        else:
            return self._timezone

    def set_apply_times_daily(self, apply_times_daily: bool):
        self._apply_time_daily = apply_times_daily
        return self

    def apply_times_daily(self, apply_times_daily=None):
        if apply_times_daily is not None:
            return self.set_apply_times_daily(apply_times_daily)
        else:
            return self._apply_time_daily

    def set_running_query_flag(self, running_query_flag: bool):
        self._running_query_flag = running_query_flag
        return self

    def running_query_flag(self, running_query_flag=None):
        if running_query_flag is not None:
            return self.set_running_query_flag(running_query_flag)
        else:
            return self._running_query_flag

    def set_query_properties(self, query_properties):
        self._query_properties = query_properties
        return self

    def query_properties(self, query_properties=None):
        if query_properties is not None:
            self._query_properties = query_properties
            return self
        else:
            return self._query_properties

    def set_query_params(self, query_params):
        self._query_params = query_params
        return self

    def query_params(self, query_params=None):
        if query_params is not None:
            self._query_params = query_params
            return self
        else:
            return self._query_params

    def set_symbol_date(self, symbol_date):
        self._symbol_date = symbol_date
        return self

    def symbol_date(self, symbol_date=None):
        if symbol_date is not None:
            self._symbol_date = symbol_date
            return self
        else:
            return self._symbol_date

    def set_symbols(self, symbols):
        if isinstance(symbols, pd.DataFrame):
            self.symbols_ = get_symbols_from_pandas(symbols)
        elif isinstance(symbols, SymbolResultMap) or isinstance(symbols, SymbolResultList):
            self.symbols_ = _graph_components.get_symbols_list_from_result(symbols)
        elif isinstance(symbols, Query):
            self.symbols_ = f'eval({symbols.unique_name})'
        else:
            self.symbols_ = symbols[:]
        return self

    def symbols(self, symbols=None):
        if symbols is not None:
            return self.set_symbols(symbols)
        else:
            return self.symbols_

    def set_symbol(self, symbol):
        if isinstance(symbol, Query):
            self.symbols_ = f'eval({symbol.unique_name})'
        else:
            self.symbols_ = [symbol]
        return self

    def symbol(self, symbol):
        return self.set_symbol(symbol)

    def set_http_address(self, http_address):
        self._http_address = http_address
        return self

    def http_address(self, http_address=None):
        if http_address is not None:
            return self.set_http_address(http_address)
        else:
            return self._http_address

    def set_http_username(self, http_username):
        self._http_username = http_username
        return self

    def http_username(self, http_username=None):
        if http_username is not None:
            return self.set_http_username(http_username)
        else:
            return self._http_username

    def set_http_password(self, http_password):
        self._http_password = http_password
        return self

    def http_password(self, http_password=None):
        if http_password is not None:
            return self.set_http_password(http_password)
        else:
            return self._http_password

    def set_access_token(self, access_token):
        self._access_token = access_token
        return self

    def access_token(self, access_token=None):
        if access_token is not None:
            return self.set_access_token(access_token)
        else:
            return self._access_token

    def set_trusted_certificate_file(self, trusted_certificate_file):
        self._trusted_certificate_file = trusted_certificate_file
        return self

    def trusted_certificate_file(self, trusted_certificate_file=None):
        if trusted_certificate_file is not None:
            return self.set_trusted_certificate_file(trusted_certificate_file)
        else:
            return self._trusted_certificate_file

    def set_max_concurrency(self, max_concurrency):
        self._max_concurrency = max_concurrency
        return self

    def max_concurrency(self, max_concurrency=None):
        if max_concurrency is not None:
            return self.set_max_concurrency(max_concurrency)
        else:
            return self._max_concurrency

    @staticmethod
    def _delete_old_temp_svg_files(dir_path=None, file_prefix="OmdExtApiRender"):
        if dir_path is None:
            dir_path = _tempfile.gettempdir()
        for file in os.listdir(dir_path):
            if file.startswith(file_prefix):
                file_path = os.path.join(dir_path, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)

    def render(self, file_path=None, img_format="svg", render_in_jupiter=True, view=True, verbose=False):
        """
        Renders the query to file and optionally displays it.
        If no file_path is specified then the rendered result is saved in the system tmp dir.
        If view is set to False then the rendered result will not be displayed.

        Keyword arguments:
        file_path (string, default: None(save in tmp dir)) :
            File path for storing rendered result.
        format (string, default: svg) :
            Format for storing rendered result(svg, pdf, png etc.).
        view (boolean, default: True) :
            Display the rendered result.
        """
        if not graphviz_imported:
            raise OneTickException("Please, install graphviz and dot to use the render() function",
                                   ErrorTypes.ERROR_GENERIC, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)

        def in_ipynb():
            try:
                return True if get_ipython().config else False
            except NameError:
                return False

        def display_graph_in_jupyter(graph):
            from IPython.display import display
            display(graph)

        if not in_ipynb():
            render_in_jupiter = False

        # delete old svg files from temp folder
        QueryCommonProperties._delete_old_temp_svg_files()

        graph_renderer = self._construct_query_for_render(verbose=verbose)

        if file_path is None:
            file_path = _tempfile.gettempdir() + "/OmdExtApiRender" + create_unique_file_name()

        graph_renderer.format = img_format

        if render_in_jupiter:
            display_graph_in_jupyter(graph_renderer)
        else:
            graph_renderer.render(file_path, view=view)


class ChainQuery(QueryCommonProperties):
    """
    Class representing OneTick chain queries
    """

    def __init__(self, *eps_param):
        """
        Constructs a chain query from the list of event processors.

        Positional arguments:
        eps (variadic list of EventProcessors) :
            List of event processors for this chain query.
        """
        QueryCommonProperties.__init__(self)
        self.chain_ = []
        self.tick_types_ = []
        self._query_alias = None
        self.add(*eps_param)
        self._caller = sys._getframe(1).f_code.co_filename

    def _construct_chain_query(self):
        eps_list = []
        for ep in self.chain_:
            ep_parameters_class = ep.__class__.Parameters
            ep_param_attributes = ep_parameters_class.list_parameters()
            ep_param_vals = ','.join(
                [f'{ep_parameters_class.__dict__[param_name]}="{str(getattr(ep, param_name))}"'
                 for param_name in ep_param_attributes])
            eps_list.append(ep.name_ + "(" + ep_param_vals + ")")
        query_str = ','.join(eps_list) + ';' + '+'.join(self.tick_types_)
        if self._query_alias is not None:
            query_str += ' ' + self._query_alias
        return query_str

    def add(self, *elements):
        """
        Adds specified event processors to the chain query(from the end).

        Positional arguments:
        elements (variadic list of EventProcessors) :
            List of event processors and/or Chainlet to add to this chain query(from the end).

        Returns :
            Reference to this chain query.
        """
        for elem in elements:
            if isinstance(elem, _graph_components.Chainlet):
                for ep in elem:
                    self.chain_.append(ep.copy())
            else:
                if (isinstance(elem, _graph_components.EpBase) and (elem.sources_ or elem.sinks_)) or (isinstance(
                        elem, _graph_components.EpBase.PinnedEp) and (elem._ep.sources_ or elem._ep.sinks_)):
                    raise OneTickException(f"{str(elem)} ep can't have sources or sinks as it is a part of chain query",
                                           ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                           getframeinfo(currentframe()).lineno)
                self.chain_.append(elem.copy())
        return self

    def __rshift__(self, ep):
        return self.add(ep)

    def set_query_alias(self, alias):
        """
        Sets chain query alias to be displayed in the output(by default the whole chain query is included in the output)
        and returns reference to current chain query

        Positional arguments:
        alias (string) :
            Query alias to be displayed in the output.

        Returns :
            Reference to current chain query.
        """
        self._query_alias = alias
        return self

    def query_alias(self, alias=None):
        """
        1. Sets chain query alias if callback parameter is passed(returns reference to current chain query for easy
        chaining of calls)
        2. Gets output callback attached to this chain query if no callback parameter is passed.

        Keyword arguments:
        callback (PythonOutputCallback, default: None) :
            Callback for this chain query.

        Returns :
            1. Reference to current chain query if callback parameter is passed.
            2. Output callback attached to this chain query if no callback parameter is passed.
        """
        if alias is not None:
            return self.set_query_alias(alias)
        else:
            return self._query_alias

    def set_tick_type(self, tick_type):
        """
        Sets tick type attached to this query and returns reference to current chain query

        Positional arguments:
        tick_type (string) :
            Tick type for this query.

        Returns :
            Reference to this chain query.
        """
        self.tick_types_ = [tick_type]
        return self

    def tick_type(self, tick_type):
        """
        Sets tick types attached to this chain query and returns reference to the chain query itself(for easy chaining
        of calls).

        Positional arguments:
        tick_type (string) :
            Tick type for this chain query.

        Returns :
            Reference to this chain query.
        """
        return self.set_tick_type(tick_type)

    def set_tick_types(self, tick_types):
        """
        Sets tick types attached to this chain query and returns reference to the chain query itself(for easy chaining
        of calls).

        Positional arguments:
        tick_types (list of strings) :
            Tick types for this node.

        Returns :
            Reference to current chain query.
        """
        self.tick_types_ = tick_types[:]
        return self

    def tick_types(self, tick_types=None):
        """
        1. Sets tick types attached to this chain query if tick_types parameter is passed(returns reference to current
        chain query for easy chaining of calls)
        2. Gets tick types attached to this chain query if no tick_types parameter is passed.

        Keyword arguments:
        tick_types (list of strings, default: None(acts as a getter)) :
            Tick types for this node. Use empty list if you want to clear the list of tick types attached to this chain
            query.

        Returns :
            1. Reference to current chain query if a parameter is passed.
            2. List of tick types attached to this chain query if no parameter is passed.

        Examples:
            1. ChainQuery().tick_types(["TRD", "QTE"]) -> create a chain query and bind TRD and QTE tick types to it
            2. chain_query=ChainQuery()
               print(chain_query.tick_types()) -> print list of tick types attached to this chain query.
        """
        if tick_types is not None:
            return self.set_tick_types(tick_types)
        else:
            return self.tick_types_

    def to_graph(self):
        """
        Constructs graph query from chain query
        """

        if self.chain_:
            root = self.chain_[0].copy()
            for elem in self.chain_[1:]:
                sink_ep = elem.copy()
                root.add_sink(sink_ep)
                root = sink_ep

            if self.tick_types_:
                root.set_tick_types(self.tick_types_)

            graph = GraphQuery(root)
            graph.symbols_ = self.symbols_
            graph._start_time = self._start_time
            graph._end_time = self._end_time
            graph._timezone = self._timezone
            graph._symbol_date = self._symbol_date
            graph._query_properties = self._query_properties
            graph._callback = self._callback
            graph._max_concurrency = self._max_concurrency
            return graph

    @staticmethod
    def _construct_chain_for_render(chain_query, verbose=False):
        graph_renderer = _gv.Digraph()
        prev_ep = None
        for ep in chain_query.chain_:
            node_label = str(ep).split('\n', 1)[0] if verbose else ep._get_name()
            if ep == chain_query.chain_[-1] and verbose:
                node_label += "\ntick_types = [" + ','.join(chain_query.tick_types_) + "]"
            graph_renderer.node(str(hex(id(ep))), node_label)
            if prev_ep is not None:
                graph_renderer.edge(str(hex(id(prev_ep))), str(hex(id(ep))))
            prev_ep = ep
        return graph_renderer

    def _construct_query_for_render(self, verbose=False):
        return ChainQuery._construct_chain_for_render(self, verbose)


class GraphQuery(QueryCommonProperties):
    """
    GraphQuery class
    """
    GraphNode = namedtuple('GraphNode', 'graph ep')

    class PinnedGraph:
        """
        The PinnedGraph class represents GraphQuery with selected input and/or output node.
        It can be used as usual GraphQuery in most cases. It is the return type of __getitem__ and __call__, input
        methods on GraphQuery object. When sunk or sourced the PinnedGraph object sinks/sources the underlying
        GraphQuery, but using fixed input/output nodes.
        """

        def __init__(self, graph, output_node=None, input_node=None):
            """
            Constructs PinnedGraph object from given GraphQuery object and the input/output nodes to use at
            sinking/sourcing
            """
            self.output_node_ = output_node
            self.input_node_ = input_node
            self.graph_ = graph

        def save_to_file(self, file_path, query_name, symbols=None, start=None, end=None, timezone=None,
                         apply_times_daily=None, query_properties=None, symbol_date=None, max_concurrency=None,
                         query_batch_size=None, start_time_expression=None, end_time_expression=None,
                         query_params=None, running_query=None):
            return self.graph_.save_to_file(
                file_path=file_path, query_name=query_name, symbols=symbols, start=start, end=end, timezone=timezone,
                apply_times_daily=apply_times_daily, query_properties=query_properties, symbol_date=symbol_date,
                max_concurrency=max_concurrency, query_batch_size=query_batch_size, query_params=query_params,
                start_time_expression=start_time_expression, end_time_expression=end_time_expression,
                running_query=running_query)

        def copy(self):
            return self.graph_.copy()

        def set_root(self, ep):
            return self.graph_.set_root(ep)

        def root(self, ep=None):
            return self.graph_.root(ep)

        def get_root(self):
            return self.graph_.get_root()

        @property
        def unique_name(self):
            return self.graph_.unique_name

        def add_sink(self, graph):
            """
            Adds the graph parameter as sink to selected(at construction or via call to __getitem__ method)
            output node of the underlying GraphQuery object
            """
            if isinstance(graph, self.__class__):
                return self.graph_.add_sink(graph.graph_, output_node=self.output_node_, input_node=graph.input_node_)
            return self.graph_.add_sink(graph, output_node=self.output_node_)

        def add_source(self, graph):
            """
            Adds the graph parameter as source to selected(at construction or via call to input or __call__ methods)
            input node of the underlying GraphQuery object
            """
            if isinstance(graph, self.__class__):
                return self.graph_.add_source(graph.graph_, output_node=graph.output_node_, input_node=self.input_node_)
            return self.graph_.add_source(graph, input_node=self.input_node_)

        def __rshift__(self, graph):
            """
            Same as add_sink
            """
            return self.add_sink(graph)

        def __lshift__(self, graph):
            """
            Same as add_source
            """
            return self.add_source(graph)

        def input(self, input_node_name):
            return self.graph_.input(input_node_name)

        def __call__(self, input_node_name):
            return self.graph_.input(input_node_name)

        def __getitem__(self, item):
            return self.graph_.__getitem__(item)

    def __init__(self, component=None):
        """
        Constructs a graph from any component of the graph.

        Keyword arguments:
        component (EventProcessor or Chainlet) :
            Some part of the graph.
        """
        QueryCommonProperties.__init__(self)
        if isinstance(component, _graph_components.Chainlet):
            self.root_ = component.last()
        elif isinstance(component, _graph_components.EpBase):
            self.root_ = component
        elif isinstance(component, _graph_components.EpBase.PinnedEp):
            self.root_ = component._ep
        else:
            raise OneTickException('Trying to construct a graph from a component of type different from EventProcessor '
                                   'or Chainlet.', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        self.otq_file_name_ = None
        self.sinks_ = defaultdict(list)
        self.sources_ = defaultdict(list)
        self._caller = sys._getframe(1).f_code.co_filename
        self.query_name = "Graph_1"

    def copy(self):
        """
        Returns a copy of the GraphQuery. No relations between graphs are copied
        """
        copy_state = {}
        return self._copy_impl(copy_state)

    def _copy_impl(self, copy_state, keep_indexes=False):
        root_copy = self.root_.copy(keep_indexes=keep_indexes)
        cls = self.__class__
        new_copy = cls.__new__(cls)
        cls.__init__(new_copy, root_copy)

        new_copy.set_symbols(_copy.copy(self.symbols()))
        new_copy.set_symbol_date(_copy.copy(self._symbol_date))
        new_copy.set_query_properties(_copy.copy(self.query_properties()))
        new_copy.set_query_params(_copy.copy(self.query_params()))
        new_copy.set_start_time(_copy.copy(self.start_time()))
        new_copy.set_end_time(_copy.copy(self.end_time()))
        new_copy.set_timezone(_copy.copy(self.timezone()))
        new_copy.set_empty_valid_params(_copy.copy(self.empty_valid_params()))
        new_copy.set_callback(_copy.copy(self.callback()))
        new_copy.set_apply_times_daily(_copy.copy(self.apply_times_daily()))
        new_copy.set_running_query_flag(_copy.copy(self.running_query_flag()))
        new_copy.set_max_concurrency(_copy.copy(self.max_concurrency()))
        new_copy.set_root(self._copy_eps(self.root_, self.root_.copy(keep_indexes=keep_indexes), None, copy_state, keep_indexes=keep_indexes))
        return new_copy

    def _copy_eps(self, cur_ep, copy_cur_ep, parent_ep, copy_state, keep_indexes=False):
        copy_state[cur_ep] = copy_cur_ep

        for sink in cur_ep.sinks_:
            if sink._ep == parent_ep:
                continue
            if sink._ep not in copy_state:
                sink_ep_ = sink._ep.copy(keep_indexes=keep_indexes)
                copy_cur_ep.add_sink(sink_ep_, output_name=sink._output_name, input_name=sink._input_name)
                if sink.propagation_order_ != -1:
                    copy_cur_ep.set_propagation_order_for_sink(sink_ep_, sink.propagation_order_,
                                                               output_name=sink._output_name,
                                                               input_name=sink._input_name)
                self._copy_eps(sink._ep, sink_ep_, cur_ep, copy_state, keep_indexes=keep_indexes)
            else:
                copy_cur_ep.add_sink(copy_state[sink._ep], output_name=sink._output_name, input_name=sink._input_name)
                if sink.propagation_order_ != -1:
                    copy_cur_ep.set_propagation_order_for_sink(copy_state[sink._ep], sink.propagation_order_,
                                                               output_name=sink._output_name,
                                                               input_name=sink._input_name)

        for source in cur_ep.sources_:
            if source._ep == parent_ep:
                continue
            if source._ep not in copy_state:
                source_ep_ = source._ep.copy(keep_indexes=keep_indexes)
                copy_cur_ep.add_source(source_ep_, output_name=source._output_name, input_name=source._input_name)
                if source.propagation_order_ != -1:
                    source_ep_.set_propagation_order_for_sink(copy_cur_ep, source.propagation_order_,
                                                              output_name=source._output_name,
                                                              input_name=source._input_name)
                self._copy_eps(source._ep, source_ep_, cur_ep, copy_state, keep_indexes=keep_indexes)
            else:
                copy_cur_ep.add_source(copy_state[source._ep], output_name=source._output_name,
                                       input_name=source._input_name)
                if source.propagation_order_ != -1:
                    copy_state[source._ep].set_propagation_order_for_sink(copy_cur_ep, source.propagation_order_,
                                                                          output_name=source._output_name,
                                                                          input_name=source._input_name)
        return copy_cur_ep

    def preprocess_graph(self, cur_ep, copy_cur_ep, parent_ep, dfs_state, copy_state, copy_new_graph_state,
                         copy_eps_state, parent_graph=None):
        dfs_state[cur_ep] = 0
        copy_state.add(cur_ep)

        for sink in cur_ep.sinks_:
            if sink._ep == parent_ep:
                continue
            if sink._ep not in copy_state:
                self.preprocess_graph(sink._ep, copy_eps_state[sink._ep], cur_ep, dfs_state, copy_state,
                                      copy_new_graph_state, copy_eps_state, self)

        for source in cur_ep.sources_:
            if source._ep == parent_ep:
                continue
            if source._ep not in copy_state:
                self.preprocess_graph(source._ep, copy_eps_state[source._ep], cur_ep, dfs_state, copy_state,
                                      copy_new_graph_state, copy_eps_state, self)

        if cur_ep in self.sinks_:
            for sink in self.sinks_[cur_ep]:
                if sink.graph == parent_graph:
                    continue
                if sink.ep not in copy_new_graph_state:
                    copy_new_graph_state[sink.ep] = self._copy_eps(sink.ep, sink.ep.copy(), None, copy_eps_state)
                copy_sink_ep = copy_new_graph_state[sink.ep]
                if sink.ep in copy_state:
                    if dfs_state[sink.ep] == 1:
                        copy_cur_ep.add_sink(copy_sink_ep)
                else:
                    copy_cur_ep.add_sink(copy_sink_ep)
                    sink.graph.preprocess_graph(sink.ep, copy_sink_ep, cur_ep, dfs_state, copy_state,
                                                copy_new_graph_state, copy_eps_state, self)

        if cur_ep in self.sources_:
            for source in self.sources_[cur_ep]:
                if source.graph == parent_graph:
                    continue
                if source.ep not in copy_new_graph_state:
                    copy_new_graph_state[source.ep] = self._copy_eps(source.ep, source.ep.copy(), None, copy_eps_state)
                copy_source_ep = copy_new_graph_state[source.ep]
                if source.ep in copy_state:
                    if dfs_state[source.ep] == 1:
                        copy_cur_ep.add_source(copy_source_ep)
                else:
                    copy_cur_ep.add_source(copy_source_ep)
                    source.graph.preprocess_graph(source.ep, copy_source_ep, cur_ep, dfs_state, copy_state,
                                                  copy_new_graph_state, copy_eps_state, self)

        dfs_state[cur_ep] = 1
        return

    def _change_root_if_needed(self):
        if isinstance(self.root_, _graph_components.EpBase):
            component = self.root_
            while len(component.sinks_) > 0:
                component = component.sinks_[0]._ep
            self.root_ = component
        elif isinstance(self.root_, _graph_components.EpBase.PinnedEp):
            component = self.root_
            while len(component._ep.sinks_) > 0:
                component._ep = component._ep.sinks_[0]._ep
            self.root_ = component._ep

    def deep_copy(self, keep_indexes=False):
        copy_eps_state = {}
        graph = self._copy_impl(copy_eps_state, keep_indexes=keep_indexes)
        dfs_state = {}
        copy_state = set()
        copy_new_graph_state = {}
        self.preprocess_graph(self.root_, graph.root_, None, dfs_state, copy_state, copy_new_graph_state, copy_eps_state)
        graph._change_root_if_needed()
        return graph

    def set_root(self, ep):
        """
        Sets graph's root(any event processor in constructed graph) and returns reference to the GraphQuery itself
        .

        Positional arguments:
        ep (EventProcessor) :
            Root event processor.

        Returns :
            Reference to this graph query.
        """
        self.root_ = ep
        return self.root_

    def root(self, ep=None):
        """
        1. Sets graph's root(any event processor in constructed graph) and returns reference to the GraphQuery itself
        if ep parameter is specified.
        2. Returns current graph's root if ep parameter is not specified.

        Keyword arguments:
        ep (EventProcessor, default: None) :
            Root event processor.

        Returns :
            1. Reference to this graph query if ep parameter is specified.
            2. Current graph query root if ep parameter is not specified
        """
        if ep is not None:
            self.root_ = ep
            return self
        else:
            return self.root_

    def get_root(self):
        return self.root_

    @property
    def unique_name(self):
        if self.otq_file_name_ is None:
            return self.unique_name_impl()
        return self.otq_file_name_

    def unique_name_impl(self, symbols=None, start=None, end=None, timezone=None, apply_times_daily=None,
                         query_properties=None, symbol_date=None, max_concurrency=None, query_batch_size=None,
                         start_time_expression=None, end_time_expression=None, query_params=None, running_query=None,
                         http_info: HttpConnectionInfo = None):
        """
        Returns a name of in memory otq file constructed from the graph.
        If the result is directly passed to a constructor of an EP(e.g. JoinWithQuery(otq_query=" + g.unique_name + "))
        the file will be automatically removed from memory upon ep destruction.
        """
        if self.otq_file_name_ is None:
            self.otq_file_name_ = create_unique_query_file_name(self)
            self.save_to_file(file_path=self.otq_file_name_, query_name=self.query_name, symbols=symbols,
                              start=start, end=end, timezone=timezone, apply_times_daily=apply_times_daily,
                              query_properties=query_properties, symbol_date=symbol_date,
                              max_concurrency=max_concurrency, query_batch_size=query_batch_size,
                              start_time_expression=start_time_expression, end_time_expression=end_time_expression,
                              query_params=query_params, save_in_memory_only=True, running_query=running_query,
                              http_info=http_info)
        return self.otq_file_name_

    def save_to_file(self, file_path, query_name=None, symbols=None, start=None, end=None, timezone=None,
                     apply_times_daily=None, query_properties=None, symbol_date=None, max_concurrency=None,
                     query_batch_size=None, start_time_expression=None, end_time_expression=None, query_params=None,
                     save_in_memory_only=False, running_query=None, http_info: HttpConnectionInfo = None):
        # we want to save the copy of the graph in order do not modify the original graph
        graph_copy = self.deep_copy()
        if symbols is None:
            symbols = self.symbols()
        if isinstance(symbols, str) or isinstance(symbols, Symbol):
            symbols = [symbols]
        if symbol_date is None:
            symbol_date = self.symbol_date()
        if start is None:
            start = self.start_time()
        if end is None:
            end = self.end_time()
        if start_time_expression is None:
            start_time_expression = self.start_time_expression()
        if end_time_expression is None:
            end_time_expression = self.end_time_expression()
        if timezone is None:
            timezone = self.timezone()
        if apply_times_daily is None:
            apply_times_daily = self.apply_times_daily()
        if query_params is None:
            query_params = self.query_params()
        if query_properties is None:
            query_properties = self.query_properties()
        if running_query is None:
            running_query = self.running_query_flag()
        start = datetime_to_str(start)
        end = datetime_to_str(end)
        return graph_copy._save_to_file_impl(
            ep=graph_copy.root_, file_path=file_path, query_name=query_name, timezone=timezone,
            apply_times_daily=apply_times_daily, save_in_memory_only=save_in_memory_only, start=start, end=end,
            symbols=symbols, query_properties=query_properties, symbol_date=symbol_date, query_params=query_params,
            max_concurrency=max_concurrency, query_batch_size=query_batch_size, running_query=running_query,
            start_time_expression=start_time_expression, end_time_expression=end_time_expression, http_info=http_info)

    def _save_to_file_impl(self, ep, file_path, query_name, symbols=None, start=None, end=None, timezone=None,
                           apply_times_daily=None, query_properties=None, symbol_date=None, max_concurrency=None,
                           query_batch_size=None, start_time_expression=None, end_time_expression=None,
                           query_params=None, save_in_memory_only=False, running_query=None,
                           http_info: HttpConnectionInfo = None):
        dfs_state = {}
        copy_state = set()
        otq_str = self._generate_otq_graph(
            ep, None, dfs_state, copy_state, symbols=symbols, query_name=query_name, symbol_date=symbol_date,
            query_batch_size=query_batch_size, query_properties=query_properties, query_params=query_params,
            max_concurrency=max_concurrency, http_info=http_info)
        otq_str += GraphQuery.generate_meta_section_str(
            apply_times_daily=apply_times_daily, start=start, end=end, start_time_expression=start_time_expression,
            end_time_expression=end_time_expression, timezone=timezone, running_query=running_query)

        save_in_memory(file_path, otq_str, 1000 * time.time())
        if not save_in_memory_only:
            f = open(file_path, "w", encoding="utf-8")
            f.write(otq_str)
            f.close()

    @staticmethod
    def get_file_name(otq_name):
        file_path = otq_name
        real_otq_name = otq_name
        if not otq_name.startswith("remote"):
            index = otq_name.find("::")
            if index != -1:  # [full/or/relative/path/]myotq.otq::Graph_1
                file_path = otq_name[0:index]
        else:
            index = otq_name.find("::")
            index2 = otq_name.find("::", index + 2)
            if index2 == -1:  # remote://<DBNAME>::[full/or/relative/path/]myotq.otq
                file_path = otq_name[index + 2:]
                real_otq_name = file_path
            else:  # remote://<DBNAME>::[full/or/relative/path/]myotq.otq::Graph_1
                file_path = otq_name[index + 2:index2]
                real_otq_name = otq_name[index + 2:]
        return file_path, real_otq_name

    @staticmethod
    def download_remote_file(remote_file, http_info: HttpConnectionInfo = None):
        index = remote_file.find("::")
        index2 = remote_file.find("::", index + 2)
        file_symbol = remote_file[len("remote://"):]
        query_name = ""
        remote_file_name = remote_file
        if index2 != -1:  # remote://<DBNAME>::[full/or/relative/path]::[query_name]
            file_symbol = remote_file[len("remote://"):index2]
            query_name = remote_file[index2 + 2:]
            remote_file_name = remote_file[:index2]
        if remote_file_name not in cached_memory_files:
            request_params = {
                "query_type": "chain",
                "symbols": [file_symbol],
                "queries": [
                    "CSV_FILE_LISTING(STORE_FILE_IN_ONE_FIELD=true,HANDLE_FILE_AS_REMOTE_OTQ=true,FILE_OPENING_MODE=binary); FILE"],
                "s": "20010101000000",
                "e": "20010101001000",
                "timezone": "GMT",
                "response": "arrow"
            }
            data = execute_streaming_query(request_params, http_info=http_info)
            file_content = data[file_symbol]["COLUMN1"][0]
            save_in_memory(remote_file_name, file_content, 1000 * time.time())
        content, last_modification_time = get_from_memory(remote_file_name)
        return content, query_name

    @staticmethod
    def get_nested_in_out_pins(cur_ep, http_info: HttpConnectionInfo = None):
        nested_inputs = {}
        nested_outputs = {}
        if isinstance(cur_ep, _ep.NestedOtq):
            tmp_file_flag = False
            if cur_ep.otq_name.startswith("remote://"):
                file_content, query_name = GraphQuery.download_remote_file(cur_ep.otq_name, http_info=http_info)
                with _tempfile.NamedTemporaryFile(mode='w', suffix=".otq", delete=False) as tmp:
                    tmp.write(file_content)
                    file_name = tmp.name
                    tmp_file_flag = True
                real_otq_name = file_name
                if query_name:
                    real_otq_name = file_name + "::" + query_name
            else:
                file_name, real_otq_name = GraphQuery.get_file_name(cur_ep.otq_name)
                if not os.path.exists(file_name) and cur_ep.otq_name not in cached_memory_files:
                    raise OneTickException(f'Nested otq file {file_name} does not exists',
                                           ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                                           getframeinfo(currentframe()).lineno)
            otq_file = OtqFile()
            otq_file.load_from_file(real_otq_name)
            queries = otq_file.queries()
            if len(queries) == 0:
                raise OneTickException(f'Otq file {real_otq_name} does not contain queries in it',
                                       ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                                       getframeinfo(currentframe()).lineno)
            if len(queries) > 1:
                raise OneTickException(f'Otq file {real_otq_name} contains more than 1 queries',
                                       ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                                       getframeinfo(currentframe()).lineno)
            query = list(queries.values())[0]
            nested_inputs = query.nested_inputs()
            nested_outputs = query.nested_outputs()
            if tmp_file_flag:
                os.remove(file_name)
        return nested_inputs, nested_outputs

    @staticmethod
    def _generate_sink_str(sink, nested_inputs, nested_outputs, http_info: HttpConnectionInfo = None):
        if not sink._output_name and not sink._input_name:
            return sink._ep.extra_parameters_['node_index'] + " "
        else:
            if isinstance(sink._ep, _ep.NestedOtq):
                nested_inputs, tmp = GraphQuery.get_nested_in_out_pins(sink._ep, http_info=http_info)
            input_name = sink._input_name
            if input_name in nested_inputs:
                input_name = nested_inputs[input_name]
            output_name = sink._output_name
            if output_name in nested_outputs:
                output_name = nested_outputs[output_name]
            return sink._ep.extra_parameters_['node_index'] + "." + output_name + "." + input_name + " "

    @staticmethod
    def _generate_source_str(source, nested_inputs, nested_outputs, http_info: HttpConnectionInfo = None):
        if not source._output_name and not source._input_name:
            return source._ep.extra_parameters_['node_index'] + " "
        else:
            if isinstance(source._ep, _ep.NestedOtq):
                tmp, nested_outputs = GraphQuery.get_nested_in_out_pins(source._ep, http_info=http_info)
            input_name = source._input_name
            if input_name in nested_inputs:
                input_name = nested_inputs[input_name]
            output_name = source._output_name
            if output_name in nested_outputs:
                output_name = nested_outputs[output_name]
            return source._ep.extra_parameters_['node_index'] + "." + input_name + "." + output_name + " "

    def _generate_otq_graph(
            self, cur_ep, parent_ep, dfs_state, copy_state, first_time=True, query_properties=None, symbols=None,
            query_name=None, symbol_date=None, query_batch_size=None, query_params=None, max_concurrency=None,
            http_info: HttpConnectionInfo = None, replace_memory_files=False):
        otq_str = self._generate_otq_graph_impl(
            cur_ep=cur_ep, parent_ep=parent_ep, dfs_state=dfs_state, copy_state=copy_state, first_time=first_time,
            query_properties=query_properties, symbols=symbols, query_name=query_name, symbol_date=symbol_date,
            query_batch_size=query_batch_size, query_params=query_params, max_concurrency=max_concurrency,
            http_info=http_info, replace_memory_files=replace_memory_files)
        otq_str += "TYPE = GRAPH\n"
        if self.timezone():
            otq_str += f"TZ = {self.timezone()}\n"
        return otq_str

    def _generate_otq_graph_impl(self, cur_ep, parent_ep, dfs_state, copy_state, first_time=True, query_properties=None,
                                 symbols=None, query_name=None, symbol_date=None, query_batch_size=None,
                                 query_params=None, max_concurrency=None, http_info: HttpConnectionInfo = None,
                                 replace_memory_files=False):
        otq_str = ""
        node_name = cur_ep.extra_parameters_['node_index']
        if first_time:
            first_time = False
            if query_name:
                otq_str += f"[{query_name}]\n"
            else:
                otq_str += "[Graph_1]\n"
            query_max_concurrency = self.max_concurrency() if max_concurrency is None else max_concurrency
            query_max_concurrency = 1 if query_max_concurrency is None else query_max_concurrency
            otq_str += f"CPU_NUMBER = {query_max_concurrency}\n"
            if query_batch_size:
                otq_str += f"QUERY_BATCH_SIZE = {query_batch_size}\n"
            if self.running_query_flag():
                otq_str += f"RunningQuery = 1\n"
            query_symbol_date = symbol_date if symbol_date else self.symbol_date()
            query_symbol_date = date_to_str(query_symbol_date)
            if query_symbol_date is None:
                query_symbol_date = 0
            query_symbols = symbols if symbols else self.symbols()
            if isinstance(query_symbols, str):
                otq_str += f"SECURITY = {query_symbols} {query_symbol_date}\n"
            else:
                for symbol in query_symbols:
                    if not isinstance(symbol, Symbol):
                        otq_str += f"SECURITY = {symbol} {query_symbol_date}\n"
                    else:
                        otq_str += f"SECURITY = {symbol.name} {query_symbol_date}\n"
                        if symbol.params:
                            params_str = f"SECURITY_PARAM = {onetick_repr(symbol.name)}"
                            for param, value in symbol.params.items():
                                params_str += f" {onetick_repr(param)} {onetick_repr(str(value))}"
                            otq_str += params_str + "\n"
            query_properties = query_properties if query_properties else self.query_properties()
            if query_properties and isinstance(query_properties, QueryProperties):
                query_properties_dict = query_properties.get_properties()
                for key in query_properties_dict:
                    otq_str += f"{key} = {query_properties_dict[key]}\n"
            query_params = query_params if query_params else self.query_params()
            if query_params and isinstance(query_params, dict):
                for param in query_params:
                    otq_str += f"PARAMETER = {param} {query_params[param]}\n"
            empty_valid_params = self.empty_valid_params()
            if empty_valid_params and isinstance(empty_valid_params, list):
                for key, value in empty_valid_params:
                    otq_str += f"PARAMETER_VALID_IF_EMPTY = {key} {value}\n"
            node_name = "ROOT"
        nested_inputs = {}
        nested_outputs = {}
        if isinstance(cur_ep, _ep.NestedOtq):
            nested_inputs, nested_outputs = GraphQuery.get_nested_in_out_pins(cur_ep, http_info=http_info)
            if replace_memory_files and cur_ep.otq_name.startswith("memory"):
                idx = cur_ep.otq_name.find("::")
                if idx == -1:
                    raise OneTickException(f'Internal error, query name is not specified {cur_ep.otq_name}', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                           getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
                nested_query_name = cur_ep.otq_name[idx:]
                otq_str += f"{node_name}=NESTED_OTQ ___ME___{nested_query_name}\n"
            else:
                otq_str += f"{node_name}=NESTED_OTQ {cur_ep.otq_name}\n"
            if cur_ep.otq_parameters:
                nested_otq_params = cur_ep.otq_parameters
                i = 0
                params_len = len(nested_otq_params)
                quote_open1 = False
                quote_open2 = False
                key_search = True
                p_key = ""
                kv_list = list()
                while i < params_len:
                    if key_search:
                        while nested_otq_params[i] == ' ' or nested_otq_params[i] == ',':
                            i = i + 1
                        index = nested_otq_params.find('=', i)
                        if index == -1:
                            raise OneTickException(
                                f'Nested otq parameters should be like key1=value1,key2=value2,... however '
                                f'{nested_otq_params} was specified', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
                        p_key = nested_otq_params[i:index].strip()
                        key_search = False
                        i = index + 1
                    else:
                        while nested_otq_params[i] == ' ':
                            i = i + 1
                        if nested_otq_params[i] == '"' or nested_otq_params[i] == "'":
                            if nested_otq_params[i] == '"':
                                quote_open2 = True
                            if nested_otq_params[i] == "'":
                                quote_open1 = True
                            j = i + 1
                            while j < params_len:
                                if nested_otq_params[j - 1] != '\\' and (
                                        (nested_otq_params[j] == '"' and quote_open2) or
                                        (nested_otq_params[j] == "'" and quote_open1)):
                                    p_value = nested_otq_params[i:j + 1]
                                    kv_list.append((p_key, p_value))
                                    key_search = True
                                    i = j + 1
                                    break
                                else:
                                    j = j + 1
                        else:
                            quote_open1 = False
                            quote_open2 = False
                            j = i
                            index = params_len
                            while j < params_len:
                                if nested_otq_params[j] == '"' and nested_otq_params[j - 1] != '\\' and not quote_open1:
                                    quote_open2 = not quote_open2
                                if nested_otq_params[j] == "'" and nested_otq_params[j - 1] != '\\' and not quote_open2:
                                    quote_open1 = not quote_open1
                                if nested_otq_params[j] == ',' and nested_otq_params[j - 1] != '\\' and \
                                        not (quote_open2 or quote_open1):
                                    index = j
                                    break
                                j = j + 1
                            p_value = nested_otq_params[i:index]
                            kv_list.append((p_key, p_value))
                            key_search = True
                            i = index + 1

                for key, value in kv_list:
                    value = value.replace("\\=", "=")
                    quote_open1 = False
                    quote_open2 = False
                    new_value = ""
                    j = 0
                    while j < len(value):
                        if value[j] == '"' and value[j - 1] != '\\' and not quote_open1:
                            quote_open2 = not quote_open2
                        if value[j] == "'" and value[j - 1] != '\\' and not quote_open2:
                            quote_open1 = not quote_open1
                        if value[j] == '\\' and value[j + 1] == ',' and \
                                not (quote_open2 or quote_open1):
                            j = j + 1
                        new_value = new_value + value[j]
                        j = j + 1
                    otq_str += f"{node_name}_PARAMETER = {key} {new_value}\n"
        else:
            otq_str += f"{node_name}={repr(cur_ep)}\n"
        if cur_ep.node_name_:
            otq_str += f"{node_name}_NAME={cur_ep.node_name_}\n"

        if cur_ep.tick_types_:
            otq_str += f"{node_name}_TICK_TYPE={'+'.join(x for x in cur_ep.tick_types_)}\n"

        if cur_ep.process_node_locally_:
            otq_str += f"{node_name}_PROCESS_LOCALLY = 1\n"

        if cur_ep.output_data_:
            otq_str += f"{node_name}_DATA_OUTPUT = 1\n"

        for input_name, pin_name in cur_ep.input_pin_names_.items():
            otq_str += f"{node_name}_NESTED_INPUT = {pin_name}\n"
        for output_name, pin_name in cur_ep.output_pin_names_.items():
            otq_str += f"{node_name}_NESTED_OUTPUT = {pin_name}\n"

        if cur_ep.symbols_:
            if isinstance(cur_ep.symbols_, str):
                otq_str += f"{node_name}_BIND_SECURITY = {cur_ep.symbols_} 0\n"
            else:
                for symbol in cur_ep.symbols_:
                    if not isinstance(symbol, Symbol):
                        otq_str += f"{node_name}_BIND_SECURITY = {symbol} 0\n"
                    else:
                        otq_str += f"{node_name}_BIND_SECURITY = {symbol.name} 0\n"
                        if symbol.params:
                            params_str = f"{node_name}_BIND_SECURITY_PARAM = {symbol.name}"
                            for param, value in symbol.params.items():
                                params_str += f" {param} {value}"
                            otq_str += params_str + "\n"

        dfs_state[cur_ep] = 0
        copy_state.add(cur_ep)

        sinks_str = ""
        for sink in cur_ep.sinks_:
            if sink._ep == parent_ep:
                continue
            if sink._ep in copy_state:
                if dfs_state[sink._ep] == 1:
                    sinks_str += GraphQuery._generate_sink_str(sink, nested_inputs, nested_outputs, http_info=http_info)
            else:
                sinks_str += GraphQuery._generate_sink_str(sink, nested_inputs, nested_outputs, http_info=http_info)
                otq_str += self._generate_otq_graph_impl(sink._ep, cur_ep, dfs_state, copy_state, first_time=first_time,
                                                         http_info=http_info, replace_memory_files=replace_memory_files)
        if sinks_str:
            otq_str += f"{node_name}_SINK = {sinks_str}\n"

        sources_str = ""
        for source in cur_ep.sources_:
            if source._ep == parent_ep:
                continue
            if source._ep in copy_state:
                if dfs_state[source._ep] == 1:
                    sources_str += GraphQuery._generate_source_str(source, nested_inputs, nested_outputs,
                                                                   http_info=http_info)
            else:
                sources_str += GraphQuery._generate_source_str(source, nested_inputs, nested_outputs,
                                                               http_info=http_info)
                otq_str += self._generate_otq_graph_impl(source._ep, cur_ep, dfs_state, copy_state,
                                                         first_time=first_time, http_info=http_info, replace_memory_files=replace_memory_files)
        if sources_str:
            otq_str += f"{node_name}_SOURCE = {sources_str}\n"

        dfs_state[cur_ep] = 1
        return otq_str
    
    @staticmethod
    def generate_otq_sql_section(sql_query, query_name=None, max_concurrency=None):
        name = query_name if query_name else sql_query.query_name()
        if not name:
            name = "Sql_1"

        cpu_number = max_concurrency if (isinstance(max_concurrency, int) and max_concurrency > 0) else 1

        sql_text = sql_query.sql_statement()
        if sql_text is None:
            sql_text = sql_query._sql_statement
        if sql_text is None:
            sql_text = ""

        lines: list[str] = []
        lines.append(f"[{name}]")
        lines.append("COMMENT = ")
        lines.append(f"CPU_NUMBER = {cpu_number}")
        lines.append("DB_HINT_FOR_PROCESSING_HOST = ")
        lines.append("NESTED_OTQS_USE_ONLY_SINKS_FOR_OUTPUT = TRUE")
        lines.append("NO_COORDS = 1")
        lines.append("one_to_many_symbol_mapping = 0")
        lines.append("QUERY_BATCH_SIZE = 0")
        lines.append("SHOW_TEMPLATE = ")

        parts = str(sql_text).splitlines()
        if len(parts) <= 1:
            lines.append(f"SQL = {str(sql_text).strip()}")
        else:
            start, end = 0, len(parts)
            while start < end and parts[start].strip() == "":
                start += 1
            while end > start and parts[end - 1].strip() == "":
                end -= 1
            core = [(ln.rstrip().rstrip("\\")) for ln in parts[start:end]]
            lines.append("SQL = \\")
            lines.append("\\\n".join(core) + "\\")
            lines.append("")

        lines.append("TYPE = SQL")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def generate_meta_section_str(apply_times_daily=None, start=None, end=None, timezone=None,
                                  start_time_expression=None, end_time_expression=None, running_query=None):
        otq_str = "\n[_meta]\n"
        if apply_times_daily is None:
            apply_times_daily = False
        otq_str += f"ApplyTimesDaily = {apply_times_daily}\n"
        if start is None:
            start = "19700101010101"
        otq_str += f"start = {start}\n"
        if start_time_expression:
            otq_str += f"start_expression = {start_time_expression}\n"
        if end is None:
            end = "19700101010101"
        otq_str += f"end = {end}\n"
        if end_time_expression:
            otq_str += f"end_expression = {end_time_expression}\n"
        if timezone is None:
            timezone = ""
        otq_str += f"TZ = {timezone}\n"
        if running_query is None:
            running_query = False
        otq_str += f"RunningQuery = {int(running_query)}\n"
        otq_str += "file_version = 1.0\n"
        return otq_str

    @staticmethod
    def save_queries_to_file(graphs, file_path, query_names, symbols=None, start=None, end=None,
                             timezone=None, apply_times_daily=None, query_properties=None, symbol_date=None,
                             max_concurrency=None, query_batch_size=None, start_time_expression=None,
                             end_time_expression=None, query_params=None, running_query=None,
                             save_in_memory_only=False, replace_memory_files=False):
      
        otq_str = ""
        if len(graphs) != len(query_names):
            raise OneTickException('`graphs` and `query_names` must be same length', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

        for (graph, query_name) in zip(graphs, query_names):
            if isinstance(graph, GraphQuery):
                graph_copy = graph.deep_copy(keep_indexes=True)
                dfs_state = {}
                copy_state = set()
                otq_str += graph_copy._generate_otq_graph(
                    graph_copy.root_, None, dfs_state, copy_state, symbols=symbols, query_name=query_name,
                    symbol_date=symbol_date, query_batch_size=query_batch_size, query_properties=query_properties,
                    query_params=query_params, max_concurrency=max_concurrency, replace_memory_files=replace_memory_files)
            elif isinstance(graph, SqlQuery):
                otq_str += GraphQuery.generate_otq_sql_section(
                    sql_query=graph,
                    query_name=query_name,
                    max_concurrency=max_concurrency
                )
            else:
                raise OneTickException('`graphs` must be a list of GraphQuery objects', ErrorTypes.ERROR_INVALID_INPUT,
                                       getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
            start = start if start else graph.start_time()
            end = end if end else graph.end_time()
            if start_time_expression is None:
                start_time_expression = graph.start_time_expression()
            if end_time_expression is None:
                end_time_expression = graph.end_time_expression()
            timezone = timezone if timezone else graph.timezone()
            apply_times_daily = apply_times_daily if apply_times_daily else graph.apply_times_daily()

        start = datetime_to_str(start)
        end = datetime_to_str(end)
        otq_str += GraphQuery.generate_meta_section_str(
            apply_times_daily=apply_times_daily, start=start, end=end, timezone=timezone, running_query=running_query,
            start_time_expression=start_time_expression, end_time_expression=end_time_expression)
        save_in_memory(file_path, otq_str, 1000 * time.time())
        if not save_in_memory_only:
            f = open(file_path, "w", encoding="utf-8")
            f.write(otq_str)
            f.close()

    def get_input_and_output_nodes(self):
        output_nodes = []
        input_nodes = []
        dfs_state = {}
        self._get_input_and_output_nodes_recursive(self.root_, input_nodes, output_nodes, dfs_state)
        return input_nodes, output_nodes

    def _get_input_and_output_nodes_recursive(self, ep, input_nodes, output_nodes, dfs_state):
        dfs_state[ep] = 1
        if len(ep.sinks_) == 0 and ep not in output_nodes:
            output_nodes.append(ep)
        if len(ep.sources_) == 0 and ep not in input_nodes:
            input_nodes.append(ep)

        for source in ep.sources_:
            if source._ep not in dfs_state:
                self._get_input_and_output_nodes_recursive(source._ep, input_nodes, output_nodes, dfs_state)
        for sink in ep.sinks_:
            if sink._ep not in dfs_state:
                self._get_input_and_output_nodes_recursive(sink._ep, input_nodes, output_nodes, dfs_state)

    def input(self, input_node_name):
        """Select an input node of the GraphQuery
        (The returned object is a wrapper on the GraphQuery, which when sunk from other GraphQueries will use the
        selected input node).

        Positional arguments :
        input_node_name(String) :
            The name of an input node

        Returns :
            PinnedGraph object, which in most cases is same as GraphQuery.
        """
        nodes = self.get_input_and_output_nodes()
        node = None
        for source in nodes[0]:
            name = source.node_name() or source.name_
            if name == input_node_name:
                if node is None:
                    node = source
                else:
                    raise OneTickException(f'Multiple input EventProcessors have same node_name: {input_node_name}',
                                           ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                           getframeinfo(currentframe()).lineno)
        if node is None:
            raise OneTickException(f"GraphQuery doesn't have an input node with specified name: {input_node_name}",
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        return self.PinnedGraph(self, input_node=node)

    def __call__(self, input_name):
        """Same as input method
        """
        return self.input(input_name)

    def __getitem__(self, output_node_name):
        """Select an output node for GraphQuery (The returned object is a wrapper on the GraphQuery, which when
        sourced to other GraphQueries will use the selected output node).

        Positional arguments :
        output_node_name(String) :
            The name of an output node

        Returns :
            PinnedGraph object, which in most cases is same as GraphQuery.
        """
        nodes = self.get_input_and_output_nodes()
        node = None
        for sink in nodes[1]:
            name = sink.node_name() or sink.name_
            if name == output_node_name:
                if node is None:
                    node = sink
                else:
                    raise OneTickException(f'Multiple output EventProcessors have same node_name: {output_node_name}',
                                           ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                           getframeinfo(currentframe()).lineno)
        if node is None:
            raise OneTickException(f"GraphQuery doesn't have an output node with specified name: {output_node_name}",
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        return self.PinnedGraph(self, output_node=node)

    def add_sink(self, graph, output_node=None, input_node=None):
        """Adds the passed GraphQuery as a child of the current GraphQuery (current GraphQuery's output node will
        feed its data to the specified GraphQuery's input node(that nodes are selected via __getitem__ and input
        methods correspondingly))

        Positional arguments :
        graph(GraphQuery) :
            Child GraphQuery

        Returns :
            Reference to child graph.
        """
        if isinstance(graph, self.PinnedGraph):
            self.add_sink(graph.graph_, output_node, graph.input_node_)
            return graph

        nodes = self.get_input_and_output_nodes()
        if output_node is None:
            if len(nodes[1]) != 1:
                raise OneTickException(f'Expected 1 output node, but found {len(nodes[1])}',
                                       ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                       getframeinfo(currentframe()).lineno)
            else:
                output_node = nodes[1][0]
        elif output_node not in nodes[1]:
            raise OneTickException('specified output_node is not an output node for the GraphQuery:',
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)

        graph_nodes = graph.get_input_and_output_nodes()
        if input_node is None:
            if len(graph_nodes[0]) != 1:
                raise OneTickException(f'Expected 1 input node, but found {len(nodes[0])}',
                                       ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                       getframeinfo(currentframe()).lineno)
            else:
                input_node = graph_nodes[0][0]
        elif input_node not in graph_nodes[0]:
            raise OneTickException('specified input_node is not an input node for the GraphQuery:',
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)

        self.sinks_[output_node].append(self.GraphNode(graph=graph, ep=input_node))
        graph.sources_[input_node].append(self.GraphNode(graph=self, ep=output_node))
        return graph

    def __rshift__(self, other):
        """Same as add_sink method
        """
        return self.add_sink(other)

    def add_source(self, graph, output_node=None, input_node=None):
        """Adds the passed GraphQuery as a source of the current GraphQuery (current GraphQuery's input node will
        receive data from the specified GraphQuery's output node(that nodes are selected via input and __getitem__
        methods correspondingly))

        Positional arguments :
        graph(GraphQuery) :
            Source GraphQuery.

        Returns :
            Reference to source GraphQuery.
        """
        if isinstance(graph, self.PinnedGraph):
            self.add_source(graph.graph_, graph.output_node_, input_node)
            return graph

        graph_nodes = graph.get_input_and_output_nodes()
        if output_node is None:
            if len(graph_nodes[1]) != 1:
                raise OneTickException(f'Expected 1 output node, but found {len(graph_nodes[1])}',
                                       ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                       getframeinfo(currentframe()).lineno)
            else:
                output_node = graph_nodes[1][0]
        elif output_node not in graph_nodes[1]:
            raise OneTickException('specified output_node is not an output node for the GraphQuery:',
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)

        nodes = self.get_input_and_output_nodes()
        if input_node is None:
            if len(nodes[0]) != 1:
                raise OneTickException(f'Expected 1 input node, but found {len(nodes[0])}',
                                       ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                       getframeinfo(currentframe()).lineno)
            else:
                input_node = nodes[0][0]
        elif input_node not in nodes[0]:
            raise OneTickException('specified input_node is not an input node for the GraphQuery:',
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)

        self.sources_[input_node].append(self.GraphNode(graph=graph, ep=output_node))
        graph.sinks_[output_node].append(self.GraphNode(graph=self, ep=input_node))
        return graph

    def __lshift__(self, other):
        """Same as add_source method
        """
        return self.add_source(other)

    @staticmethod
    def _construct_graph_for_render(graph_query, verbose=False):
        graph_renderer = _gv.Digraph()
        dfs_state = {}
        GraphQuery._construct_graph_for_render_recursive(graph_query.root_, None, dfs_state, graph_renderer, verbose)
        return graph_renderer

    @staticmethod
    def _construct_graph_for_render_recursive(cur_ep, parent_ep, dfs_state, graph_render, verbose):
        dfs_state[cur_ep] = 1
        graph_render.node(str(hex(id(cur_ep))), str(cur_ep) if verbose else cur_ep._get_name())
        for sink in cur_ep.sinks_:
            if sink._ep == parent_ep:
                continue
            graph_render.edge(str(hex(id(cur_ep))), str(hex(id(sink._ep))), taillabel=sink._output_name,
                              headlabel=sink._input_name)
            if sink._ep not in dfs_state or dfs_state[sink._ep] == 0:
                GraphQuery._construct_graph_for_render_recursive(sink._ep, cur_ep, dfs_state, graph_render, verbose)
        for source in cur_ep.sources_:
            if source._ep == parent_ep:
                continue
            if source._ep not in dfs_state or dfs_state[source._ep] == 0:
                GraphQuery._construct_graph_for_render_recursive(source._ep, cur_ep, dfs_state, graph_render, verbose)
                graph_render.edge(str(hex(id(source._ep))), str(hex(id(cur_ep))), taillabel=source._output_name,
                                  headlabel=source._input_name)

    def _construct_query_for_render(self, verbose=False):
        return GraphQuery._construct_graph_for_render(self, verbose)


Graph = GraphQuery


class SqlQuery(QueryCommonProperties):
    """Class representing OneTick sql queries"""

    def __init__(self, sql_statement=None):
        """Constructs sql query from sql statement string.
        Keyword arguments:
        sql_statement(string).
            The sql statement string.
        """
        QueryCommonProperties.__init__(self)
        self._sql_statement = sql_statement
        self._merge_all_symbols_flag = None
        self._separate_dbname_flag = None
        self._query_name = 'Sql_1'
        
    def set_query_name(self, query_name):
        """Sets query name and returns reference to the query itself.

		Positional arguments:
		query_name (string):
			Query name.

		Returns :
			Reference to this query.
		"""
        self._query_name = query_name
        return self

    def query_name(self, query_name=None):
        """
		1. Sets query name and returns reference to the query itself if query_name parameter is specified.
		2. Gets query name if query_name parameter is not specified.

		Keyword arguments:
		query_name (string, default: None):
			Query name.

		Returns :
			1. Reference to this query if query_name parameter is specified.
			2. Query name if query_name parameter is not specified.
		"""
        if query_name is not None:
            return self.set_query_name(query_name)
        else:
            return self._query_name

    def set_sql_statement(self, sql_statement):
        """Sets sql statement and returns reference to the query itself.

        Positional arguments:
        sql_statement(string):
            The sql statement string.

        Returns:
            Reference to this query.
        """
        self._sql_statement = sql_statement
        return self

    def sql_statement(self, sql_statement=None):
        """
        1. Sets sql statement for this query and returns reference to the query itself if statement parameter is
        specified.
        2. Gets sql statement for this query if statement parameter is not specified.

        Keyword arguments:
        statement(string, default: None):
            The sql statement string.

        Returns:
            1. Reference to this query if statement parameter is specified.
            2. Sql statement string if statement parameter is not specified.
        """
        if sql_statement is None:
            return self._sql_statement
        return self.set_sql_statement(sql_statement)

    def set_merge_all_symbols_flag(self, merge_all_symbols_flag):
        """Sets merge_all_symbols flag and returns reference to the query itself.

        Positional arguments:
        merge_all_symbols_flag(boolean):
            If set to true, ticks returned by the query for all symbols get merged into a single time series.

        Returns:
            Reference to this query.
        """
        self._merge_all_symbols_flag = merge_all_symbols_flag
        return self

    def merge_all_symbols_flag(self, merge_all_symbols_flag=None):
        """
        1. Sets merge_all_symbols flag for this query and returns reference to the query itself if
        merge_all_symbols_flag parameter is specified.
        2. Gets merge_all_symbols flag for this query if merge_all_symbols_flag parameter is not specified.

        Keyword arguments:
        merge_all_symbols_flag(boolean, default: None):
            The merge_all_symbols flag.

        Returns:
            1. Reference to this query if merge_all_symbols_flag parameter is specified.
            2. merge_all_symbols flag if merge_all_symbols_flag parameter is not specified.
        """
        if merge_all_symbols_flag is None:
            return self._merge_all_symbols_flag
        return self.set_merge_all_symbols_flag(merge_all_symbols_flag)

    def set_separate_dbname_flag(self, separate_dbname_flag):
        """Sets separate_dbname flag and returns reference to the query itself.

        Positional arguments: separate_dbname_flag(boolean): If set to true, and merge_all_symbols_flag is set to
        true, SYMBOL_NAME field contains a symbol name without the database name, and DB_NAME field contains the
        database name for a symbol.

        Returns:
            Reference to this query.
        """
        self._separate_dbname_flag = separate_dbname_flag

    def separate_dbname_flag(self, separate_dbname_flag=None):
        """
        1. Sets separate_dbname flag for this query and returns reference to the query itself if separate_dbname_flag
        parameter is specified. 2. Gets separate_dbname flag for this query if separate_dbname_flag parameter is not
        specified.

        Keyword arguments:
        separate_dbname(boolean, default: None):
            The separate_dbname flag.

        Returns:
            1. Reference to this query if separate_dbname_flag parameter is specified.
            2. separate_dbname flag if separate_dbname_flag parameter is not specified.
        """
        if separate_dbname_flag is None:
            return self._separate_dbname_flag
        return self.set_separate_dbname_flag(separate_dbname_flag)


class Query(QueryCommonProperties):
    """Class representing OneTick query"""

    def __init__(self, query=None, extract_query_settings=False):

        QueryCommonProperties.__init__(self)
        self._query_name = 'Graph_1'
        self._batch_size = None
        self._batch_time_msec = None
        self._max_concurrency = None
        self._query_params = None
        self._otq_file_name = None
        self._nested_inputs = {}
        self._nested_outputs = {}

        if query is None:
            self._query = None
        else:
            self.set_query(query, extract_query_settings)

    def extract_query_settings(self, query):
        """Changes Query's settings (start_time, end_time, ...) to query's settings.

		Positional arguments:
		query (GraphQuery):
			Query object.

		Returns :
			Reference to this query.
		"""
        if isinstance(query, GraphQuery):
            self.init(query)
        else:
            raise OneTickException('unknown value for query, it should be GraphQuery',
                                   ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        return self

    def set_query(self, query, extract_query_settings=False):
        if isinstance(query, GraphQuery):
            self._query = query
        elif isinstance(query, ChainQuery):
            self._query = query.to_graph()
        elif isinstance(query, _graph_components.Chainlet):
            self._query = GraphQuery(query)
        else:
            raise OneTickException('unknown value for query, it should be GraphQuery, ChainQuery, OtqQuery or Chainlet',
                                   ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        if extract_query_settings:
            self.extract_query_settings(self._query)
        return self

    def query(self, query=None):
        if query is not None:
            return self.set_query(query)
        else:
            return self._query

    def set_query_name(self, query_name):
        """Sets query name and returns reference to the query itself.

		Positional arguments:
		query_name (string):
			Query name.

		Returns :
			Reference to this query.
		"""
        self._query_name = query_name
        return self

    def query_name(self, query_name=None):
        if query_name is not None:
            return self.set_query_name(query_name)
        else:
            return self._query_name

    def set_batch_size(self, batch_size):
        self._batch_size = batch_size
        return self

    def batch_size(self, batch_size=None):
        if batch_size is not None:
            return self.set_batch_size(batch_size)
        else:
            return self._batch_size

    def set_batch_time_msec(self, batch_time_msec):
        self._batch_time_msec = batch_time_msec
        return self

    def batch_time_msec(self, batch_time_msec=None):
        if batch_time_msec is not None:
            return self.set_batch_time_msec(batch_time_msec)
        else:
            return self._batch_time_msec

    def set_nested_inputs(self, nested_inputs):
        self._nested_inputs = nested_inputs
        return self

    def nested_inputs(self, nested_inputs=None):
        if nested_inputs is not None:
            return self.set_nested_inputs(nested_inputs)
        else:
            return self._nested_inputs

    def set_nested_outputs(self, nested_outputs):
        self._nested_outputs = nested_outputs
        return self

    def nested_outputs(self, nested_outputs=None):
        if nested_outputs is not None:
            return self.set_nested_outputs(nested_outputs)
        else:
            return self._nested_outputs

    @property
    def unique_name(self):
        """Returns a name of in memory otq file constructed from the Query.
		If the result is directly passed to a constructor of an EP(e.g. JoinWithQuery(otq_query=" + q.unique_name + "))
		the file will be automatically removed from memory upon ep destruction.
		"""
        if self._otq_file_name is None:
            if self._query is not None:
                self._query.init(self)
            self._otq_file_name = create_unique_query_file_name(self._query)
            otq_file = OtqFile([self])
            otq_file.save_to_file(self._otq_file_name + "::" + self.query_name(), save_in_memory_only=True)
        return self._otq_file_name + "::" + self.query_name()

    def run(self, context='DEFAULT', username=None, output_structure=OutputStructure.symbol_result_map, callback=None,
            cancellation_handle=None, use_python_style_nulls_for_missing_values=None, compression="zstd",
            output_mode=QueryOutputMode.numpy, treat_byte_arrays_as_strings=True, encoding='utf-8'):
        """Processes this query and returns numpy arrays from the node that are marked to return data.
		Keyword arguments:
		context (string, default: DEFAULT) :
			The context of the query
		return_utc_times (boolean, default: False):
			If true Return times in UTC timezone and in local timezone otherwise.
		treat_byte_arrays_as_strings (boolean, default: False):
			Output byte arrays as strings. By default, we output byte arrays.
		time_as_nsec (boolean, default: False):
			Output timestamps up to nanoseconds granularity.
			By default, we output timestamps in microseconds granularity.
		output_matrix_per_field (boolean, default: False):
			Changes output format to list of matrices per field.
		output_structure (OutputStructure, default: OutputStructure.symbol_result_map):
			Specifies the structure of output.

		Returns:
			If output_structure is OutputStructure.symbol_result_map(default) returns
			onetick.query.query.SymbolResultMap object, which is a convenient wrapper on NumpyOnetickQuery output,
			described in NumPy_OneTick_query.html output section case 3. Otherwise, if the output_structure is
			OutputStructure.symbol_result_list a raw list of format described in
			NumPy_OneTick_query.html output section case 1 is returned.
		"""

        if callback is None:
            callback = self.callback()
        return _run_internal(query=self._query, http_address=self._http_address, bs_ticks=self._batch_size, bs_time_msec=self._batch_time_msec,
                   symbols=self.symbols(), username=username, context=context, timezone=self._timezone, query_properties=self._query_properties,
                   symbol_date=self._symbol_date, start=self._start_time, end=self._end_time, query_params=self._query_params,
                   apply_times_daily=self.apply_times_daily(), max_concurrency=self._max_concurrency, running_query_flag=self._running_query_flag,
                   output_structure=output_structure, callback=callback, cancellation_handle=cancellation_handle, access_token=self._access_token,
                   http_username=self._http_username, http_password=self._http_password, compression=compression, output_mode=output_mode,
                   use_python_style_nulls_for_missing_values=use_python_style_nulls_for_missing_values, encoding=encoding,
                   trusted_certificate_file=self._trusted_certificate_file, treat_byte_arrays_as_strings=treat_byte_arrays_as_strings)

    def save_to_file(self, file_path):
        """Saves this query to file.
		Positional arguments:
		file_path (string) :
			File path to save the query in(results in an otq file).

		Keyword arguments:
		context(string, default: DEFAULT):
			The context to be used for connection
		convert_this_to_py_file(Boolean, default: False):
			Swap THIS:: with the name of the corresponding python file.

		"""
        otq_file = OtqFile([self])
        otq_file.save_to_file(file_path)

    def load_from_file(self, otq_path):
        """Loads query from given otq file.

		Positional arguments:
		otq_path (string) :
			Otq file path to load from.

		"""
        otq_file = OtqFile()
        otq_file.load_from_file(otq_path)
        queries = otq_file.queries()
        if len(queries) == 0:
            raise OneTickException(f'Otq file {otq_path} does not contain queries in it',
                                   ErrorTypes.ERROR_INVALID_INPUT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        if len(queries) > 1:
            raise OneTickException(f'Otq file {otq_path} contains more than 1 queries', ErrorTypes.ERROR_INVALID_INPUT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        query = list(queries.values())[0]
        self.init(query)
        query.query().init(query)
        self.set_query(query.query())
        self.set_nested_inputs(query.nested_inputs())
        self.set_nested_outputs(query.nested_outputs())
        self.set_query_name(query.query_name())
        self.set_batch_size(query.batch_size())
        self.set_max_concurrency(query.max_concurrency())
        self.query().set_empty_valid_params(query.empty_valid_params())


class OtqFile:
    """Class representing collection of queries """

    def __init__(self, queries=None):
        if queries is None:
            self._queries = {}
        elif isinstance(queries, list):
            self.set_queries(queries)
        else:
            raise OneTickException('unknown value for queries, it should be list of Query objects',
                                   ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)

    def add_query(self, query):
        """Adds query object and returns reference to the OtqFile itself.

		Positional arguments:
		query (Query):
			Query object.

		Returns:
			Reference to this query.
		"""
        if isinstance(query, (Query, SqlQuery)):
            self._queries[query.query_name()] = query
        else:
            raise OneTickException('unknown value for query, it should be Query', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return self

    def get_query(self, query_name):
        """Gets query object for specified name and returns it.

		Positional arguments:
		query_name (string):
			Name of the query.

		Returns:
			Query object.
		"""
        if not isinstance(query_name, str):
            raise OneTickException('unknown value for query_name, it should be string',
                                   ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        return self._queries[query_name]

    def set_queries(self, queries):
        """Sets queries and returns reference to the OtqFile itself.

		Positional arguments:
		queries (list of Query objects):
			Queries.

		Returns:
			Reference to this query.
		"""
        self._queries = {}
        for query in queries:
            self.add_query(query)
        return self

    def queries(self, queries=None):
        """
		1. Set queries and returns reference to the OtqFile itself if queries parameter is specified.
		2. Get queries if queries parameter is not specified.

		Keyword arguments:
		queries (list of Query objects, default: None):
			Queries.

		Returns:
			1. Reference to this OtqFile if queries parameter is specified.
			2. Queries if queries parameter is not specified.
		"""
        if queries is not None:
            return self.set_queries(queries)
        else:
            return self._queries

    def save_to_file(self, file_path, save_in_memory_only=False, replace_memory_files=False):
        """
		Saves all queries to given otq file

		Positional arguments:
		file_path (string):
			File path to save the queries in.

		"""

        queries = []
        query_names = []
        for query in self._queries.values():
            if isinstance(query, SqlQuery):
                queries.append(query)                 
                query_names.append(query.query_name())
            else:
                graph_query = query.query()
                graph_query.init(query)
                queries.append(graph_query)
                query_names.append(query.query_name())

        GraphQuery.save_queries_to_file(queries, file_path, query_names, save_in_memory_only=save_in_memory_only,
                                        replace_memory_files=replace_memory_files)

    @staticmethod
    def _construct_ep(ep_name, params: dict):
        ep = _eps_factory.create_ep(ep_name)
        for name in params:
            ep.set_parameter(name.lower(), params[name])
        return ep

    @staticmethod
    def _parse_ep_str(ep_str: str):
        ep_str = ep_str.strip()
        ep_name = ep_str
        params = dict()
        index = ep_str.find('(')
        if index != -1:
            ep_name = ep_str[0:index]
            params_str = ep_str[index + 1:-1]
            params_list = params_str.split(',')
            key = ""
            for item in params_list:
                if not item:
                    continue
                value = item.strip()
                eq_index = item.find('=')
                if eq_index != -1:
                    key = item[0:eq_index].strip()
                    value = item[eq_index + 1:].strip(" \"\'")
                    params[key] = value
                else:
                    params[key] = params[key] + ", " + value.strip(" \"\'")
        return ep_name, params

    @staticmethod
    def _construct_symbols(lines_dict, security_str, security_param_str):
        # Add symbols
        tmp_symbols = {}
        symbols = []
        symbol_date = 0
        for symbol_str in lines_dict[security_str]:
            if len(symbol_str.split()) == 2:
                symbol, symbol_date = symbol_str.split()
                tmp_symbols[symbol] = {}
        for symbol_params_str in lines_dict[security_param_str]:
            params = symbol_params_str.split()
            symbol = params[0]
            for i in range(1, len(params), 2):
                tmp_symbols[symbol][params[i]] = params[i + 1]
        for symbol in tmp_symbols:
            symbols.append(Symbol(symbol, tmp_symbols[symbol]))
        return symbols, symbol_date

    def _construct_graph(self, lines_dict, cur_node_name, eps_dict, nested_inputs, nested_outputs):
        if cur_node_name not in eps_dict:
            ep_name, params = self._parse_ep_str(lines_dict[cur_node_name][0])
            eps_dict[cur_node_name] = self._construct_ep(ep_name, params)
        ep = eps_dict[cur_node_name]
        if not isinstance(ep, _graph_components.EpBase):
            raise OneTickException("Unknown class was created", ErrorTypes.ERROR_GENERIC,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

        node_name_str = f"{cur_node_name}_NAME"
        if node_name_str in lines_dict:
            output_data_str = f"{cur_node_name}_DATA_OUTPUT"
            if output_data_str in node_name_str:
                ep.set_output_data(lines_dict[node_name_str][0])
            else:
                ep.set_node_name(lines_dict[node_name_str][0])

        tick_type_str = f"{cur_node_name}_TICK_TYPE"
        if tick_type_str in lines_dict:
            ep.set_tick_type(lines_dict[tick_type_str][0])

        process_locally_str = f"{cur_node_name}_PROCESS_LOCALLY"
        if process_locally_str in lines_dict:
            ep.set_process_node_locally(lines_dict[process_locally_str][0])

        nested_input_str = f"{cur_node_name}_NESTED_INPUT"
        if nested_input_str in lines_dict:
            nested_inputs[lines_dict[nested_input_str][0]] = cur_node_name
            ep.set_input_pin_name(lines_dict[nested_input_str][0], cur_node_name)

        nested_output_str = f"{cur_node_name}_NESTED_OUTPUT"
        if nested_output_str in lines_dict:
            nested_outputs[lines_dict[nested_output_str][0]] = cur_node_name
            ep.set_output_pin_name(lines_dict[nested_output_str][0], cur_node_name)

        bind_symbol_name_str = f"{cur_node_name}_BIND_SECURITY"
        bind_symbol_param_str = f"{cur_node_name}_BIND_SECURITY_PARAM"
        bind_symbols, symbol_date = OtqFile._construct_symbols(lines_dict, bind_symbol_name_str, bind_symbol_param_str)
        if bind_symbols:
            ep.set_symbols(bind_symbols)

        node_sink_str = f"{cur_node_name}_SINK"
        if node_sink_str in lines_dict:
            sink_names = lines_dict[node_sink_str][0].split()
            for sink in sink_names:
                index = sink.find('.')
                if index == -1:
                    ep.add_sink(self._construct_graph(lines_dict, sink, eps_dict, nested_inputs, nested_outputs))
                else:
                    sink_name = sink[0:index]
                    input_name = sink[index + 1:]
                    ep.add_sink(self._construct_graph(lines_dict, sink_name, eps_dict, nested_inputs, nested_outputs),
                                input_name=input_name)

        node_source_str = f"{cur_node_name}_SOURCE"
        if node_source_str in lines_dict:
            source_names = lines_dict[node_source_str][0].split()
            for source in source_names:
                index = source.find('..')
                if index == -1:
                    ep.add_source(self._construct_graph(lines_dict, source, eps_dict, nested_inputs, nested_outputs))
                else:
                    source_name = source[0:index]
                    output_name = source[index + 2:]
                    ep.add_source(
                        self._construct_graph(lines_dict, source_name, eps_dict, nested_inputs, nested_outputs),
                        output_name=output_name)
        return ep

    def _apply_meta_section(self, lines_dict):
        apply_times_daily = bool(lines_dict["ApplyTimesDaily"][0]) if lines_dict.get("ApplyTimesDaily") else None
        start = str_to_datetime(lines_dict["start"][0]) if lines_dict.get("start") else None
        end = str_to_datetime(lines_dict["end"][0]) if lines_dict.get("end") else None
        timezone = lines_dict["TZ"][0] if lines_dict.get("TZ") else None
        running_query_flag = bool(lines_dict["RunningQuery"][0]) if lines_dict.get("RunningQuery") else None
        for query in self._queries.values():
            if query.start_time() is None:
                query.set_start_time(start)
            if query.end_time() is None:
                query.set_end_time(end)
            if query.timezone() is None:
                query.set_timezone(timezone)
            if query.apply_times_daily() is None:
                query.set_apply_times_daily(apply_times_daily)
            if query.running_query_flag() is None:
                query.set_running_query_flag(running_query_flag)

    def load_from_file(self, full_file_name):
        file_name = full_file_name
        query_name_arg = ""
        index = full_file_name.find("::")
        if index != -1:
            file_name = full_file_name[0:index]
            query_name_arg = full_file_name[index + 2:]
        if full_file_name in cached_memory_files:
            lines = cached_memory_files[full_file_name][0].splitlines()
        else:
            with open(file_name, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        lines_dict = defaultdict(list)
        query_name = ""
        last_line_incomplete = False
        incomplete_key = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if last_line_incomplete:
                if line[-1] == '\\':
                    line = line[:-1] + '\n'
                else:
                    last_line_incomplete = False
                lines_dict[incomplete_key][0] = lines_dict[incomplete_key][0] + line
                continue

            eq_index = line.find('=')
            if eq_index == -1:
                if lines_dict:
                    if query_name == "_meta":
                        self._apply_meta_section(lines_dict)
                    elif query_name_arg == query_name or len(query_name_arg) == 0:
                        nested_inputs = {}
                        nested_outputs = {}
                        root = self._construct_graph(lines_dict, "ROOT", {}, nested_inputs, nested_outputs)
                        graph = GraphQuery(root)
                        query = Query(graph)
                        query.set_nested_inputs(nested_inputs)
                        query.set_nested_outputs(nested_outputs)
                        # Add symbols
                        symbols, symbol_date = OtqFile._construct_symbols(lines_dict, "SECURITY", "SECURITY_PARAM")
                        query.set_symbols(symbols)
                        query.set_symbol_date(symbol_date)
                        # Add query params
                        query_params = dict()
                        for params_str in lines_dict["PARAMETER"]:
                            key = params_str.strip()
                            index = params_str.find(' ')
                            value = ""
                            if index != -1:
                                key = params_str[0:index].strip()
                                value = params_str[index + 1:].strip()
                            query_params[key] = value
                        query.set_query_params(query_params)

                        empty_valid_params = []
                        for params_str in lines_dict["PARAMETER_VALID_IF_EMPTY"]:
                            index = params_str.find(' ')
                            if index != -1:
                                key = params_str[0:index].strip()
                                value = params_str[index + 1:].strip()
                                empty_valid_params.append((key, value))
                        query.set_empty_valid_params(empty_valid_params)

                        if "RunningQuery" in lines_dict:
                            query.set_running_query_flag(bool(lines_dict["RunningQuery"][0]))

                        query_properties = QueryProperties()
                        for prop in valid_query_properties:
                            if prop in lines_dict:
                                query_properties.set_property_value(prop, lines_dict[prop][0])
                        query.set_query_properties(query_properties)

                        query.set_query_name(query_name)
                        self.add_query(query)
                    lines_dict.clear()
                query_name = line[1:-1]
            else:
                key = line[0:eq_index].strip()
                value = line[eq_index + 1:].strip().replace("THIS::", file_name + "::")
                if value and value[-1] == '\\':
                    value = value[:-1] + '\n'
                    incomplete_key = key
                    last_line_incomplete = True
                else:
                    last_line_incomplete = False
                if value:
                    lines_dict[key].append(value)
        if query_name == "_meta":
            self._apply_meta_section(lines_dict)


def get_access_token(url, client_id, client_secret, scope=None):
    params = {"grant_type": "client_credentials"}
    if scope:
        params["scope"] = scope
    response = _requests.post(
        url,
        data=params,
        auth=(client_id, client_secret),
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise OneTickException(f"Error retrieving access token: {response.status_code} - {response.text}",
                               ErrorTypes.ERROR_INVALID_INPUT, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)


def execute_streaming_query(
        request_params, http_info: HttpConnectionInfo, request_id=None, treat_byte_arrays_as_strings=True,
        output_structure=OutputStructure.symbol_result_map, output_mode=QueryOutputMode.numpy, encoding="utf-8",
        verbose=False, callback: CallbackBase = None, cancellation_handle=None,
        use_python_style_nulls_for_missing_values=None):
    auth = None
    if http_info.http_username_:
        auth = (http_info.http_username_, http_info.http_password_)
    headers = {"Content-Type": "application/json", "Connection": "keep-alive"}
    if http_info.access_token_:
        headers["Authorization"] = f"Bearer {http_info.access_token_}"

    json_params_str = _json.dumps(request_params, ensure_ascii=False, cls=OneTickJsonEncoder)
    verify = True if http_info.trusted_certificate_file_ is None else http_info.trusted_certificate_file_

    global _cookies_cache
    server_cookies = _cookies_cache.get(http_info.url_)
    resp = _requests.post(http_info.url_,
                          data=json_params_str,
                          headers=headers,
                          auth=auth,
                          stream=True,
                          proxies=http_info.proxies_,
                          verify=verify,
                          allow_redirects=False,
                          cookies=server_cookies)
    if resp.is_redirect:
        if open_id_imported:
            resp, server_cookies = open_id.get_code_flow_data_results(resp, headers, verify, http_info.proxies_)
            _cookies_cache[http_info.url_] = server_cookies
        else:
            raise OneTickException("In order to use code flow authentication functionality please pip install PySide6 library.",
                                   ErrorTypes.ERROR_GENERIC, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
    arrow_parser = ArrowParser(verbose=verbose, encoding=encoding,
                               treat_byte_arrays_as_strings=treat_byte_arrays_as_strings, callback=callback,
                               use_python_style_nulls_for_missing_values=use_python_style_nulls_for_missing_values)

    if not resp.ok:
        _cookies_cache.pop(http_info.url_,None)
        raise OneTickException(str(resp.content, 'UTF-8'), ErrorTypes.ERROR_GENERIC,
                               getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

    if http_info.url_ not in _cookies_cache:
        server_cookies = resp.cookies
        _cookies_cache[http_info.url_] = server_cookies
        if _config.API_CONFIG['ENABLE_DEBUG_LOGS'] == 1:
            print(f"Server cookies = {server_cookies}")
    if cancellation_handle is not None:
        cancellation_handle_id = resp.headers.get('Cancellation-handle')
        if cancellation_handle_id is None or cancellation_handle_id == '':
            raise OneTickException("server does not send Cancellation-handle header.", ErrorTypes.ERROR_GENERIC,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        cancellation_handle._initialize(http_info, auth, headers, cancellation_handle_id, server_cookies)

    content_type = resp.headers.get("Content-Type")
    if content_type == 'application/zstd':
        resp.raw.headers.update({'Content-Encoding': resp.raw.headers.get("Content-Encoding") or 'zstd'})
    elif content_type == "application/gzip":
        resp.raw.headers.update({'Content-Encoding': resp.raw.headers.get("Content-Encoding") or 'gzip'})

    use_arrow_send_msg_buffer_size = False
    webapi_protocol_version = resp.headers.get("Omd-Webapi-Protocol-Version")
    if webapi_protocol_version and int(webapi_protocol_version) >= 1:
        use_arrow_send_msg_buffer_size = True

    if use_arrow_send_msg_buffer_size:
        try:
            buffer = BytesQueueBuffer()
            source = resp.iter_content(chunk_size=None)

            while True:
                needed = 8
                while len(buffer) < needed:
                    buffer.put(next(source))
                chunk = buffer.get(needed)

                needed = int.from_bytes(chunk, byteorder='little')
                while len(buffer) < needed:
                    buffer.put(next(source))
                chunk = buffer.get(needed)

                arrow_parser.process_chunk(chunk, http_info, auth, headers, request_id, server_cookies)
        except StopIteration:
            pass
    else:
        for chunk in resp.iter_content(chunk_size=None):
            arrow_parser.process_chunk(chunk, http_info, auth, headers, request_id, server_cookies)

    arrow_parser.done()

    if not callback:
        return arrow_parser.get_result(output_structure, output_mode)


def with_default(val, fallback):
    return fallback if val is None else val

def run(query, http_address=None, bs_ticks=None, bs_time_msec=None, symbols=None, username=None, context=None, timezone=None, query_properties=None,
        symbol_date=None, start=None, end=None, apply_times_daily=None, query_params=None, max_concurrency=None, compression=None,
        http_username=None, http_password=None, running_query_flag=None, query_name=None, output_structure=None,
        output_mode=None, encoding=None, treat_byte_arrays_as_strings=None, callback: CallbackBase = None,
        start_time_expression=None, end_time_expression=None, cancellation_handle=None, svg_path=None, access_token=None, http_proxy=None,
        https_proxy=None, use_python_style_nulls_for_missing_values=None, trusted_certificate_file=None, __webapi_arrow_params={}):

    http_address = with_default(http_address, config.http_address)
    bs_ticks = with_default(bs_ticks, config.bs_ticks)
    bs_time_msec = with_default(bs_time_msec, config.bs_time_msec)
    symbols = with_default(symbols, config.symbols)
    username = with_default(username, config.username)
    context = with_default(context, config.context)
    timezone = with_default(timezone, config.timezone)
    query_properties = with_default(query_properties, config.query_properties)
    symbol_date = with_default(symbol_date, config.symbol_date)
    start = with_default(start, config.start)
    end = with_default(end, config.end)
    apply_times_daily = with_default(apply_times_daily, config.apply_times_daily)
    query_params = with_default(query_params, config.query_params)
    max_concurrency = with_default(max_concurrency, config.max_concurrency)
    compression = with_default(compression, config.compression)
    http_username = with_default(http_username, config.http_username)
    http_password = with_default(http_password, config.http_password)
    running_query_flag = with_default(running_query_flag, config.running_query_flag)
    query_name = with_default(query_name, config.query_name)
    output_structure = with_default(output_structure, config.output_structure)
    output_mode = with_default(output_mode, config.output_mode)
    encoding = with_default(encoding, config.encoding)
    treat_byte_arrays_as_strings = with_default(treat_byte_arrays_as_strings, config.treat_byte_arrays_as_strings)
    callback = with_default(callback, config.callback)
    start_time_expression = with_default(start_time_expression, config.start_time_expression)
    end_time_expression = with_default(end_time_expression, config.end_time_expression)
    svg_path = with_default(svg_path, config.svg_path)
    access_token = with_default(access_token, config.access_token)
    http_proxy = with_default(http_proxy, config.http_proxy)
    https_proxy = with_default(https_proxy, config.https_proxy)
    use_python_style_nulls_for_missing_values = with_default(use_python_style_nulls_for_missing_values,
                                                             config.use_python_style_nulls_for_missing_values)
    trusted_certificate_file = with_default(trusted_certificate_file, config.trusted_certificate_file)

    return _run_internal(query, http_address, bs_ticks, bs_time_msec, symbols, username, context, timezone, query_properties,
        symbol_date, start, end, apply_times_daily, query_params, max_concurrency, compression,
        http_username, http_password, running_query_flag, query_name, output_structure,
        output_mode, encoding, treat_byte_arrays_as_strings, callback,
        start_time_expression, end_time_expression, cancellation_handle, svg_path, access_token, http_proxy,
        https_proxy, use_python_style_nulls_for_missing_values, trusted_certificate_file, __webapi_arrow_params)


def _run_internal(query, http_address, bs_ticks=None, bs_time_msec=None, symbols=None, username=None, context=None, timezone=None, query_properties=None,
        symbol_date=None, start=None, end=None, apply_times_daily=None, query_params=None, max_concurrency=None, compression=None,
        http_username=None, http_password=None, running_query_flag=None, query_name=None, output_structure=OutputStructure.symbol_result_map,
        output_mode=QueryOutputMode.numpy, encoding=None, treat_byte_arrays_as_strings=None, callback: CallbackBase = None,
        start_time_expression=None, end_time_expression=None, cancellation_handle=None, svg_path=None, access_token=None, http_proxy=None,
        https_proxy=None, use_python_style_nulls_for_missing_values=None, trusted_certificate_file=None, __webapi_arrow_params={}):
    start = datetime_to_str(start)
    end = datetime_to_str(end)
    symbol_date = date_to_str(symbol_date)

    otq_file_content_as_string = True
    query_content_str = ""
    sql_query = False
    query_file_name = ""

    http_info = HttpConnectionInfo(http_address, http_username, http_password, access_token, http_proxy, https_proxy, trusted_certificate_file)

    if isinstance(symbols, str) or isinstance(symbols, Symbol):
        symbols = [symbols]

    if query_name is not None and not isinstance(query, str):
        raise OneTickException("query_name parameter could be specified only in case of otq file path",
                               ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                               getframeinfo(currentframe()).lineno)

    pass_webapi_params = False

    # should be set only for Graph/Chain/Query
    override_default_max_concurrency = False
    if isinstance(query, str):
        query_file_name = query
        pass_webapi_params = True
        override_default_max_concurrency = False
        if not query_file_name.startswith("remote"):
            index = query_file_name.find("::")
            if index != -1:  # [full/or/relative/path/]myotq.otq::Graph_1
                otq_file_path = query_file_name[0:index]
                otq_file_query_name = query_file_name[index + 2:]
                if query_name:
                    print("[WARNING] query_name parameter from arguments list will be ignored as query name '" +
                          otq_file_query_name + "' is part of provided otq file path")
                query_name = otq_file_query_name
                query_file_name = otq_file_path
            otq_file_content_as_string = False
        else:
            query_content_str, query_name = GraphQuery.download_remote_file(query_file_name, http_info=http_info)
    elif isinstance(query, GraphQuery) or isinstance(query, Query) or isinstance(query, ChainQuery):
        if isinstance(query, ChainQuery):
            query = query.to_graph()
        elif isinstance(query, Query):
            graph_query = query.query()
            graph_query.init(query)
            query = graph_query

        query._change_root_if_needed()
        start = query.start_time() if start is None else start
        end = query.end_time() if end is None else end
        query_properties = query.query_properties() if query_properties is None else query_properties
        max_concurrency = query.max_concurrency() if max_concurrency is None else max_concurrency
        http_info.trusted_certificate_file_ = query.trusted_certificate_file() if trusted_certificate_file is None else trusted_certificate_file
        override_default_max_concurrency = max_concurrency is None

        start = datetime_to_str(start)
        end = datetime_to_str(end)

        timezone = query.timezone() if timezone is None else timezone

        if isinstance(symbols, pd.DataFrame):
            symbols = get_symbols_from_pandas(symbols)
        if not symbols:
            symbols = query.symbols()
        if isinstance(symbols, SymbolResultMap) or isinstance(symbols, SymbolResultList):
            symbols = _graph_components.get_symbols_list_from_result(symbols)

        query.otq_file_name_ = None
        query_file_name = query.unique_name_impl(
            symbols=symbols, symbol_date=symbol_date, start=start, end=end, timezone=timezone,
            query_params=query_params, apply_times_daily=apply_times_daily, query_properties=query_properties,
            max_concurrency=max_concurrency, start_time_expression=start_time_expression,
            end_time_expression=end_time_expression, running_query=running_query_flag, http_info=http_info)
        otq_file_content_as_string = False
    elif isinstance(query, SqlQuery):
        query_content_str = query.sql_statement()
        sql_query = True
        override_default_max_concurrency = False
    else:
        raise OneTickException("Unsupported query type passed to process method. Here support otq file path, base64 "
                               "encoded otq content or Graph object", ErrorTypes.ERROR_UNSUPPORTED,
                               getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

    if output_mode is QueryOutputMode.callback:
        if callback is None and isinstance(query, QueryCommonProperties):
            callback = query.callback()
        if callback is None:
            raise OneTickException("callback is not specified", ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
    else:
        callback = None

    request_id = str(uuid.uuid4())
    if not sql_query:
        base64_query_str = base64.b64encode(query_content_str.encode('utf-8')).decode('utf-8')
        request_params = {'otq': base64_query_str if otq_file_content_as_string else query_file_name,
                          'query_type': "otq",
                          'otq_file_content_as_string': str(otq_file_content_as_string)
                          }
        if query_name is not None:
            request_params['sub_query'] = query_name
    else:
        # we know here that query is SqlQuery type
        request_params = {'statement': query_content_str,
                          'query_type': "sql"
                          }
        if query.merge_all_symbols_flag() is not None:
            request_params['merge_all_symbols'] = str(query.merge_all_symbols_flag())
        if query.separate_dbname_flag() is not None:
            request_params['merge_all_symbols'] = str(query.separate_dbname_flag())
    if bs_ticks is not None:
        request_params['bs_ticks'] = str(bs_ticks)
    if bs_time_msec is not None:
        request_params['bs_time_msec'] = str(bs_time_msec)
    if symbols and pass_webapi_params:
        if isinstance(symbols, SymbolResultMap) or isinstance(symbols, SymbolResultList):
            request_params['symbols'] = _graph_components.get_symbols_list_from_result(symbols)
        else:
            request_params['symbols'] = symbols

    request_params['response'] = "arrow"
    request_params['enable_per_symbol_errors'] = "True"
    request_params['request_id'] = request_id
    request_params['compression'] = compression

    if not timezone:
        timezone = get_local_timezone_name()
    request_params['timezone'] = str(timezone)
    request_params['python_tz_for_epoch_times_adjustment'] = str(timezone)

    if username is not None:
        request_params['username'] = str(username)
    if context is not None:
        request_params['context'] = str(context)

    # always prepending __WEBAPI_ARROW_SEND_MSG_BUFFER_SIZE=TRUE to query_properties as a
    # USER_DEFINED_PROPERTY

    extra_user_defined_properties_dict = {
        '__WEBAPI_ARROW_SEND_MSG_BUFFER_SIZE': 'TRUE',
        '__WEBAPI_ARROW_TREAT_BYTE_ARRAYS_AS_STRINGS': 'TRUE' if treat_byte_arrays_as_strings else 'FALSE',
        '__WEBAPI_ARROW_OUTPUT_TYPE': 'numpy' if output_mode == QueryOutputMode.callback else str(output_mode),
        '__WEBAPI_ARROW_ENCODING': encoding,
        '__WEBAPI_ARROW_OVERRIDE_DEFAULT_MAX_CONCURRENCY': override_default_max_concurrency
    }

    for key, value in __webapi_arrow_params.items():
        extra_user_defined_properties_dict[key] = value
    extra_user_defined_properties = \
        ",".join(["{}={}".format(key, value) for key, value in extra_user_defined_properties_dict.items()])

    if not query_properties:
        query_properties = QueryProperties()
    user_defined_properties = query_properties.get_user_defined_properties()
    user_defined_properties = "" if not user_defined_properties else user_defined_properties + ","
    user_defined_properties += extra_user_defined_properties

    query_properties.set_user_defined_properties(user_defined_properties)
    request_params['query_properties'] = query_properties.convert_to_name_value_pairs_string()

    if symbol_date is not None:
        request_params['symbol_date'] = str(symbol_date)
    if start is not None and pass_webapi_params:
        request_params['s'] = str(start)
    if end is not None and pass_webapi_params:
        request_params['e'] = str(end)
    if apply_times_daily is not None and not sql_query:
        request_params['apply_times_daily'] = str(apply_times_daily)
    if query_params is not None and pass_webapi_params:
        request_params['otq_params'] = convert_query_params_to_string(query_params)
    if max_concurrency is not None:
        request_params['max_concurrency'] = str(max_concurrency)
    if running_query_flag is not None and not sql_query:
        request_params['running_query'] = str(running_query_flag)

    try:
        verbose = False  # for testing purposes only
        return execute_streaming_query(
            request_params=request_params, http_info=http_info, request_id=request_id, callback=callback,
            output_structure=output_structure, output_mode=output_mode, encoding=encoding, verbose=verbose,
            treat_byte_arrays_as_strings=treat_byte_arrays_as_strings, cancellation_handle=cancellation_handle,
            use_python_style_nulls_for_missing_values=use_python_style_nulls_for_missing_values)
    except Exception as e:
        if _config.API_CONFIG['SHOW_STACK_INFO'] == 0 and _config.API_CONFIG['SHOW_STACK_WARNING'] == 1:
            print("You can set SHOW_STACK_INFO = 1 in config.py file in order to see stack information in the exception")
            print("or you can set SHOW_STACK_WARNING = 0 to disable this message.")
        if _config.API_CONFIG['RENDER_GRAPH_ON_ERROR'] == 1:
            if graphviz_imported:
                if isinstance(query, GraphQuery) or isinstance(query, ChainQuery):
                    query.render(file_path=svg_path)
            else:
                raise OneTickException(str(e) + ": Please install 'graphviz' python package to be able to render graphs",
                                       ErrorTypes.ERROR_GENERIC, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        raise e


def run_cb(query, http_address=None, bs_ticks=None, bs_time_msec=None, symbols=None, username=None, context=None, timezone=None, query_properties=None,
           symbol_date=None, start=None, end=None, apply_times_daily=None, query_params=None, max_concurrency=None, compression=None,
           http_username=None, http_password=None, running_query_flag=None, query_name=None, output_structure=None,
           encoding=None, treat_byte_arrays_as_strings=None, callback: CallbackBase = None, start_time_expression=None, end_time_expression=None,
           cancellation_handle=None, svg_path=None, access_token=None, use_python_style_nulls_for_missing_values=None, http_proxy=None,
           https_proxy=None, trusted_certificate_file=None):
    return run(query=query, http_address=http_address, bs_ticks=bs_ticks, bs_time_msec=bs_time_msec, symbols=symbols, username=username,
               context=context, timezone=timezone, query_properties=query_properties, symbol_date=symbol_date, start=start, end=end,
               apply_times_daily=apply_times_daily, query_params=query_params, max_concurrency=max_concurrency, compression=compression,
               http_username=http_username, http_password=http_password, running_query_flag=running_query_flag, query_name=query_name,
               output_structure=output_structure, output_mode=QueryOutputMode.callback, encoding=encoding,
               treat_byte_arrays_as_strings=treat_byte_arrays_as_strings, callback=callback, start_time_expression=start_time_expression,
               end_time_expression=end_time_expression, cancellation_handle=cancellation_handle, svg_path=svg_path, access_token=access_token,
               use_python_style_nulls_for_missing_values=use_python_style_nulls_for_missing_values, http_proxy=http_proxy, https_proxy=https_proxy,
               trusted_certificate_file=trusted_certificate_file)


process_callback_query = run_cb


def run_numpy(query, http_address=None, bs_ticks=None, bs_time_msec=None, symbols=None, username=None, context=None, timezone=None, query_properties=None,
              symbol_date=None, start=None, end=None, apply_times_daily=None, query_params=None, max_concurrency=None, compression=None,
              http_username=None, http_password=None, running_query_flag=None, query_name=None, output_structure=None,
              encoding=None, treat_byte_arrays_as_strings=None, start_time_expression=None, end_time_expression=None, cancellation_handle=None,
              svg_path=None, access_token=None, use_python_style_nulls_for_missing_values=None, http_proxy=None, https_proxy=None,
              trusted_certificate_file=None):
    return run(query=query, http_address=http_address, bs_ticks=bs_ticks, bs_time_msec=bs_time_msec, symbols=symbols, username=username,
               context=context, timezone=timezone, query_properties=query_properties, symbol_date=symbol_date, start=start, end=end,
               apply_times_daily=apply_times_daily, query_params=query_params, max_concurrency=max_concurrency, compression=compression,
               http_username=http_username, http_password=http_password, running_query_flag=running_query_flag, query_name=query_name,
               output_structure=output_structure, output_mode=QueryOutputMode.numpy, encoding=encoding,
               treat_byte_arrays_as_strings=treat_byte_arrays_as_strings, start_time_expression=start_time_expression,
               end_time_expression=end_time_expression, cancellation_handle=cancellation_handle, svg_path=svg_path, access_token=access_token,
               use_python_style_nulls_for_missing_values=use_python_style_nulls_for_missing_values, http_proxy=http_proxy, https_proxy=https_proxy,
               trusted_certificate_file=trusted_certificate_file)


process_numpy_query = run_numpy

"""
Decorator used in .py files which will be used as otq queries. Used to mark functions that return Query objects.
Positional arguments:
query_name (string, default: the name of the function):
	the name of the query
"""
query_creator = make_register_decorator()
