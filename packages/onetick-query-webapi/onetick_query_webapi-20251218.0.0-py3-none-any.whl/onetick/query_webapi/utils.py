import sys
from .exception import *
from .symbol import Symbol
from inspect import getframeinfo, currentframe


def attach(components, ep):
    """Links the outputs of the given components to the ep/GraphQuery specified.
	(if specified GraphQuery, all components must be GraphQueries)

	Positional arguments:
	components (list of Chainlets/ChainletOutputs/EventProcessors/PinnedEps/GraphQueries/PinnedGraphs) :
		A list consisting of Chainlet/ChainletOutputs/EventProcessors/PinnedEps/GraphQueries/PinnedGraphs.
	ep (EventProcessor/GraphQuery(PinnedGraph)) :
		The event processor/GraphQuery to link the outputs to.

	Returns :
		Returns reference to the ep/GraphQuery.
	"""
    from .query import GraphQuery
    from .graph_components import Chainlet, EpBase
    for component in components:
        if isinstance(component, Chainlet) or isinstance(component, Chainlet.ChainletOutput):
            component.link(ep)
        elif isinstance(component, EpBase) or isinstance(component, EpBase.PinnedEp) or \
                ((isinstance(component, GraphQuery) or isinstance(component, GraphQuery.PinnedGraph))
                 and (isinstance(ep, GraphQuery) or isinstance(ep, GraphQuery.PinnedGraph))):
            component.add_sink(ep)
        else:
            raise OneTickException('Trying to attach components of type different than Chainlet,ChainletOutput,'
                                   'EventProcessor,PinnedEp,GraphQuery', ErrorTypes.ERROR_INVALID_INPUT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
    return ep


def merge(components, merge_ep=None):
    """Merges given components with the specified merge_ep(which is Merge by default).

	Positional arguments:
	components (list of Chainlets/ChainletOutputs/EventProcessors/PinnedEps) :
		A list consisting of Chainlets/ChainletOutputs/EventProcessors/PinnedEps.

	Keyword arguments:
	merge_ep (EventProcessor, default: None(Merge)) :
		Merging event processor.

	Returns :
		Returns reference to the merging event processor.
	"""
    from . import ep
    if not merge_ep:
        merge_ep = ep.Merge()
    return attach(components, merge_ep)


class SymbolResultMap:
    """SymbolResultMap class is the return type of run function if output_structure is
	specified to OutputStructure.symbol_result_map and output_mode is QueryOutputMode.numpy or QueryOutputMode.pandas.
	The class is conceptually a mapping from symbol name + node_name to corresponding output dict {param_name,
	param_values} or pandas.DataFrame
	"""

    class OutputForSymbol:
        """OutputForSymbol class represents output for fixed symbol and node_name
		"""

        def __init__(self, output_tuple, label_name):
            """Constructs OutputForSymbol object
			Positional arguments:
			output_tuple ((data, errors) double tuple where data is {parameter_name(string): vals(numpy.ndarray)} or
			pandas.DataFrame and errors is a list of (error_code, error_message) double tuples):
				The output tuple which corresponds to some symbol and node_name pair.
			"""
            self._output_tuple = output_tuple
            self._label_name = label_name

        def get_data(self):
            """Returns {parameter_name(string): vals(numpy.ndarray)} dict or pandas.DataFrame, where vals is a
            numpy array of values corresponding to the given parameter. Same as data property
			"""
            return self._output_tuple[0]

        def get_error_list(self):
            """Returns a list of (error_code, error_message) double tuples and None if there were no errors. Same as
            error property
			"""
            if len(self._output_tuple[1]) == 0:
                return None
            return self._output_tuple[1]

        def get_tag(self):
            """Deprecated. Same as get_node_name. Same as tag property
			"""
            return self._label_name

        def get_node_name(self):
            """Returns the node_name of the outputting node. Same as name property
			"""
            return self._label_name

        def __str__(self):
            """Returns the string view of the underlying tuple
			"""
            return str(self._output_tuple)

        def __repr__(self):
            """Returns the string representation of the object
			"""
            return 'SymbolResultMap.{}({})'.format(self.__class__.__name__, repr(self._output_tuple))

        data = property(get_data)
        error = property(get_error_list)
        tag = property(get_tag)
        name = property(get_node_name)

    class OutputWithSelectedSymbol:
        """OutputWithSelectedSymbol class represents the SymbolResultMap object with selected symbol, but not
        selected node_name
		The node_name can be selected via __getitem__(operator []) method
		"""

        def __init__(self, node_name_to_data):
            """Constructs OutputWithSelectedSymbol object

			Positional arguments:
			node_name_to_data (dict):
				The result of selecting symbol on NumpyOnetickQuery.run_query function output.
			"""
            self._node_name_to_data = node_name_to_data

        def __getitem__(self, node_name=0):
            """Method to get the data output from node with name: node_name

			Positional arguments:
			node_name (string or integer):
				The node_name of the output node.
				The only possible integer value is special value: 0, meaning that there is only one output for given
				symbol.
				If there are more than one outputs for the given symbol and the node_name is 0 an error will be raised.
			Returns: The output for selected symbol name and node_name, which is:
			{parameter_name(string): vals(numpy.ndarray)} dict, where vals is a numpy array of values corresponding to
			the given parameter or pandas.DataFrame.
			"""
            return SymbolResultMap._get_data_from_node_name(self._node_name_to_data, node_name)

        def __iter__(self):
            """Makes OutputWithSelectedSymbol objects iterable, iteration goes over tags of output nodes
			"""
            return iter(self._node_name_to_data)

        def items(self):
            """Returns iterator over key value pairs: (node_name: String, data: dict or pandas.DataFrame).
			"""
            return SymbolResultMap.dict_items(self._node_name_to_data)

        def __repr__(self):
            """Returns the string representation of the object
			"""
            return 'SymbolResultMap.{}({})'.format(self.__class__.__name__, repr(self._node_name_to_data))

        def __str__(self):
            """Returns the string view of the object
			"""
            return str(self._node_name_to_data)

    def __init__(self, result):
        """Constructs SymbolResultMap object
		Positional arguments:

		numpy_result (dict):
			Query result returned from NumpyOnetickQuery.run_query function with output_as_dictionary=True and
			output_format_version=2.
		"""
        self._result = result
        self.node_name_ = ''  # used for sinking ep from data object
        # If you want to feed this data to other query, this flag should be False
        # Will be set to True in run_numpy, if return_utc_times=False
        self.not_utc_times_ = False

    @staticmethod
    def _get_data_from_node_name(result_dict, node_name):
        if node_name is None or node_name == 0:
            cnt = len(result_dict)
            if cnt == 0:
                raise OneTickException('The query output is empty', ErrorTypes.ERROR_INVALID_INPUT,
                                       getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
            if cnt != 1:
                raise OneTickException('There are multiple outputs for this graph, the parameter node_name should be '
                                       'specified', ErrorTypes.ERROR_INVALID_GRAPH,
                                       getframeinfo(currentframe()).filename,
                                       getframeinfo(currentframe()).lineno)
            else:
                node_name = next(iter(result_dict))
        return SymbolResultMap.OutputForSymbol(result_dict[node_name], node_name)

    @staticmethod
    def dict_items(d):
        py_version = sys.version_info[0]
        if py_version >= 3:
            return d.items()
        return d.iteritems()

    def output(self, symbol_name, node_name=0, tag=0):
        """Gives the output corresponding to given symbol name and node_name(The node_name of the output node)

		Positional arguments:
		symbol_name (string or Symbol.Symbol object):
			The name of the symbol for which the output is requested.
		Keyword arguments:
		node_name (string or integer, default: 0):
			The node_name of the output node.
			The only possible integer value is special value: 0, meaning that there is only one output for given symbol.
			If there are more than one outputs for the given symbol and the node_name is 0 an error will be raised.
		tag (string or integer, default: 0)
			Deprecated. Same as node_name
		Returns:
			SymbolResultMap.OutputForSymbol object corresponding to the given symbol and node_name.
		"""
        if node_name == 0:
            node_name = tag
        if isinstance(symbol_name, Symbol):
            symbol_name = symbol_name.name
        return SymbolResultMap._get_data_from_node_name(self._result[symbol_name], node_name)

    def __str__(self):
        """Returns string view for the underlying dictionary returned from NumpyOnetickQuery
		"""
        return str(self._result)

    def __repr__(self):
        """Returns string representation of the object
		"""
        return '{}({})'.format(self.__class__.__name__, repr(self._result))

    def __iter__(self):
        """Makes SymbolResultMap object iterable.
		Returns: an iterator which iterates over the keys of the map, the keys are Symbol.Symbol objects
		"""
        for symbol_name in self._result:
            yield Symbol(symbol_name)

    def __getitem__(self, symbol_and_node_name):
        """Provides ability to select symbol and node_name on the output using square brackets operator

		Positional arguments:
		symbol_and_node_name(symbol(string or Symbol.Symbol) or
		[symbol(string or Symbol.Symbol), node_name(string)] tuple):
			Symbol is the symbol name for which the output was requested.
			node_name is the node name of the output node.
			If the value of node_name is not supplied it means that there is only one output for given symbol.
			If there are more than one outputs for the given symbol and the node_name is not specified an error will be raised.
		Returns:
			dictionary data corresponding to given symbol, node_name pair.
		"""
        node_name = 0
        if isinstance(symbol_and_node_name, tuple):
            symbol = symbol_and_node_name[0]
            node_name = symbol_and_node_name[1]
        else:
            symbol = symbol_and_node_name
        return self.output(symbol, node_name=node_name).data

    def items(self):
        """Returns iterator over key value pairs: (Symbol.Symbol, SymbolResultMap.OutputWithSelectedSymbol).
		"""
        for symbol, result_for_smb in SymbolResultMap.dict_items(self._result):
            yield Symbol(symbol), SymbolResultMap.OutputWithSelectedSymbol(result_for_smb)

    def get_dict(self):
        """Returns the resulting dict got from NumpyOnetickQuery as is.
		"""
        return self._result

    def add_sink(self, ep):
        """Adds the current SymbolResultMap as a source of the passed event processor
		(event processor will receive data from current SymbolResultMap).

		Positional arguments:
		ep (EventProcessor):
			Sink event processor.

		Returns :
			Reference to sunk event processor.
		"""
        from . import graph_components
        if not isinstance(ep, graph_components.EpBase):
            raise OneTickException('SymbolResultMap can be source only for event processors.',
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        return ep << self

    def __rshift__(self, ep):
        """Same as add_sink
		"""
        return self.add_sink(ep)

    def node_name(self, node_name):
        self.node_name_ = node_name
        return self


# deprecated, use SymbolResultList instead
SymbolNumpyResultMap = SymbolResultMap


class SymbolResultList(list):
    """SymbolResultList class is the return type of run function if output_structure is
	specified to OutputStructure.symbol_result_list and output_mode is QueryOutputMode.numpy.
	The class is a list of (symbol_name, data) tuples, where data is a list of
	(param_name, param_values) or is a pandas.DataFrame
	"""

    def __init__(self, *args):
        super(SymbolResultList, self).__init__(*args)
        self.node_name_ = ''
        # If you want to feed this data to other query, this flag should be False
        # Will be set to True in run_numpy, if return_utc_times=False
        self.not_utc_times_ = False

    def add_sink(self, ep):
        """Adds the current SymbolResultList as a source of the passed event processor
		(event processor will receive data from current SymbolResultList).

		Positional arguments:
		ep (EventProcessor):
			Sink event processor.

		Returns :
			Reference to sunk event processor.
		"""
        from . import graph_components
        if not isinstance(ep, graph_components.EpBase):
            raise OneTickException('SymbolResultList can be source only for event processors.',
                                   ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        return ep << self

    def __rshift__(self, ep):
        """Same as add_sink
		"""
        return self.add_sink(ep)

    def node_name(self, node_name):
        self.node_name_ = node_name
        return self


# deprecated, use SymbolResultList instead
SymbolNumpyResultList = SymbolResultList


class ResultMap(dict):

    def __init__(self, *args):
        super(ResultMap, self).__init__(*args)

    class OutputForLabel:

        def __init__(self, output_tuple):
            self._output_tuple = output_tuple

        def get_data(self):
            return self._output_tuple[0]

        def get_error_list(self):
            return self._output_tuple[1]

        data = property(get_data)
        error = property(get_error_list)

        def __str__(self):
            return str(self._output_tuple)

        def __repr__(self):
            return 'ResultMap.{}({})'.format(self.__class__.__name__, repr(self._output_tuple))

    def output(self, output_label):
        if output_label not in self:
            raise OneTickException('There is no output with name {}'.format(output_label), ErrorTypes.ERROR_INVALID_INPUT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return ResultMap.OutputForLabel(self.get(output_label))

    def __getitem__(self, output_label):
        return self.output(output_label).data


def onetick_repr(obj):
    if isinstance(obj, str):
        new_repr = '"'
        for i in range(0, len(obj)):
            if obj[i] == '"' or obj[i] == '\\':
                new_repr += '\\'
            new_repr += obj[i]
        new_repr += '"'
        new_repr = new_repr.replace("\n", "\\\n")
        new_repr = new_repr.replace("\t", "    ")
        return new_repr
    return repr(obj)


def convert_query_params_to_string(query_params):
    if not isinstance(query_params, dict):
        raise OneTickException('query_params must be a dictionary.', ErrorTypes.ERROR_INVALID_ARGUMENT,
                               getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
    ans = ''
    for k, v in query_params.items():
        if isinstance(v, tuple):
            ans = ans + k + '=' + quoted(str(v[0])) + ','
        else:
            ans = ans + k + '=' + quoted(str(v)) + ','
    return ans[:-1]


def quoted(str_object):
    str_repr = repr(str_object)
    str_repr = str_repr.replace("\\\\", "\\")
    return str_repr


def get_symbols_from_pandas(symbols):
    if "SYMBOL_NAME" in symbols.columns:
        return symbols['SYMBOL_NAME'].values.tolist()
    else:
        raise OneTickException("SYMBOL_NAME column must be specified in pandas dataframe", ErrorTypes.ERROR_INVALID_ARGUMENT,
                               getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
