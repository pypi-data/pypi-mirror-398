from .graph_components import EpBase
from ._internal_utils import *
from .config import API_CONFIG
from .exception import *
from .ep import DataFileQuery

import pandas as pd
import pyarrow as pa
import urllib
from inspect import getframeinfo, currentframe


class ReadFromDataFrame(EpBase):
    """
READ_FROM_DATA_FRAME

Type: Source

Description: Reads the given pandas frame and populates each row as a tick.

Parameters:

  dataframe         - The pandas data frame to populate
  symbol_name_field - A column name in dataframe, that stores tick's symbol
  timestamp_column  - A column name in dataframe, that stores tick's timestamp
  symbol_value      - If symbol_name_field is not specified, then symbol_value should carry the value of a symbol.
                      We will add SYMBOL_NAME=symbol_value column to dataframe under the hood
    """
    class Parameters:
        data_file_ep = "DATA_FILE_EP"
        stack_info = "STACK_INFO"

        @staticmethod
        def list_parameters():
            list_val = ["data_file_ep"]
            if API_CONFIG['SHOW_STACK_INFO'] == 1:
                list_val.append("stack_info")
            return list_val

    __slots__ = ["data_file_ep", "stack_info", "_used_strings"]

    def __init__(self, dataframe=None, timestamp_column="", symbol_name_field="", symbol_value=""):
        EpBase.__init__(self, "DATA_FILE_QUERY")
        if dataframe is not None:
            if not isinstance(dataframe, pd.DataFrame):
                raise OneTickException('dataframe parameter must be a pandas dataframe type, however {} was passed'.format(type(dataframe)),
                                       ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

            if not symbol_name_field:
                dataframe['SYMBOL_NAME'] = symbol_value
            elif symbol_name_field not in dataframe.columns:
                raise OneTickException('{} is not in the list of dataframe columns'.format(symbol_name_field), ErrorTypes.ERROR_INVALID_ARGUMENT,
                                       getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

            arrow_table = pa.Table.from_pandas(dataframe)
            sink = pa.BufferOutputStream()
            with pa.ipc.RecordBatchStreamWriter(sink, arrow_table.schema) as writer:
                writer.write_table(arrow_table)
            encoded_binary_buffer = urllib.parse.quote_from_bytes(sink.getvalue().to_pybytes())
            self.data_file_ep = DataFileQuery(file_contents="expr(URLDECODE(\"{}\"))".format(encoded_binary_buffer),
                                              symbol_name_field=symbol_name_field,
                                              timestamp_column=timestamp_column)
        else:
            self.data_file_ep = None
        import sys
        frame = sys._getframe(1)
        self.stack_info = frame.f_code.co_filename + ":" + str(frame.f_lineno)

    def set_data_file_ep(self, value):
        if value and isinstance(self.data_file_ep, EpBase):
            self.data_file_ep = value.copy()
        else:
            raise OneTickException('Invalid value parameter {}'.format(value), ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return self

    def get_data_file_ep(self):
        return self.data_file_ep

    @staticmethod
    def _get_name():
        return "DATA_FILE_QUERY"

    def _to_string(self, for_repr=False):
        if self.data_file_ep and isinstance(self.data_file_ep, EpBase):
            desc = self.data_file_ep._to_string(for_repr=for_repr)
        else:
            raise OneTickException('DATA_FILE_EP is not defined', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return desc

    def __repr__(self):
        return self._to_string(for_repr=True)

    def __str__(self):
        return self._to_string()

    def __del__(self):
        for param_name in getattr(self, '_used_strings', []):
            dec_ref_count(param_name)
            if get_ref_count(param_name) == 0:
                remove_from_memory(param_name)
