import copy as _copy
from .utils import *


def get_sting_value(param):
    if hasattr(param, 'decode'):
        param = param.decode('utf-8').rstrip(' \t\r\n\0')
    return param


def get_symbols_list_from_result(symbol_results):
    from .utils import SymbolResultMap
    from .symbol import Symbol
    import pandas as pd

    if isinstance(symbol_results, SymbolResultMap):
        dictionary = True
        symbols = symbol_results.get_dict()
    elif isinstance(symbol_results, dict):
        dictionary = True
        symbols = symbol_results
    else:
        dictionary = False
        symbols = symbol_results

    is_list = not dictionary
    constructed_symbols = []
    for input_symbol in symbols:
        symbol_names = []
        if dictionary:
            fields = {}
            for label_name in symbols[input_symbol]:
                tup = symbols[input_symbol][label_name]
                for field in tup[0]:
                    if not (field in fields):
                        fields[field] = []
                    fields[field].extend(tup[0][field])
        else:
            fields = input_symbol[1]

        if "SYMBOL_NAME" not in fields:
            raise OneTickException('Unable to extract symbol names. There is no SYMBOL_NAME column',
                                   ErrorTypes.ERROR_INVALID_INPUT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        if dictionary:
            symbol_names.extend(fields["SYMBOL_NAME"])
        else:
            for field in fields:
                field_name = field if isinstance(fields, pd.DataFrame) else field[0]
                field_vals = fields[field] if isinstance(fields, pd.DataFrame) else field[1]
                if field_name == "SYMBOL_NAME":
                    symbol_names.extend(field_vals)

        params_for_symbols = [{} for _ in range(len(symbol_names))]
        for field in fields:
            if is_list:
                param_name = field if isinstance(fields, pd.DataFrame) else field[0]
                field_vals = fields[field] if isinstance(fields, pd.DataFrame) else field[1]
            else:
                param_name = field
                field_vals = fields[param_name]

            if param_name != "SYMBOL_NAME":
                for i in range(len(field_vals)):
                    param_val = field_vals[i]
                    params_for_symbols[i][get_sting_value(param_name)] = get_sting_value(param_val)
        for i in range(len(symbol_names)):
            symbol_name = get_sting_value(symbol_names[i])
            smb = Symbol(symbol_name, params_for_symbols[i])
            constructed_symbols.append(smb)
    return constructed_symbols


##
# @package onetick.query.graph_components EpBase, Chainlet documentation
#
class EpBase(object):
    """ EpBase class """
    __slots__ = ['symbols_', 'tick_types_', 'process_node_locally_', 'node_name_', 'output_data_', 'name_',
                 'extra_parameters_', 'sinks_', 'sources_', 'ep_outputs_', 'input_pin_names_', 'output_pin_names_']

    class Node:
        def __init__(self, ep, input_name="", output_name=""):
            self._ep = ep
            self._input_name = input_name
            self._output_name = output_name
            self.propagation_order_ = -1

    class Sink(Node):
        def __init__(self, ep, input_name="", output_name=""):
            EpBase.Node.__init__(self, ep, input_name, output_name)

    class Source(Node):
        def __init__(self, ep, input_name="", output_name=""):
            EpBase.Node.__init__(self, ep, input_name, output_name)

    class PinnedEp:
        """The PinnedEp class represents EP with selected input and/or output pin.
		It can be used as usual EP in most cases. It is the return type of __getitem__ and __call__, input methods on EP
		object.
		When sunk or sourced the PinnedEp object sinks/sources the underlying EP, but using fixed input/output pin names.
		"""

        def __init__(self, ep, output_name="", input_name=""):
            """Constructs PinnedEp object given EP object and the input/output pin names to use at sinking/sourcing
			"""
            self._output_name = output_name
            self._input_name = input_name
            self._ep = ep

        def add_sink(self, ep):
            """Adds the ep parameter as sink
			to the selected(at construction or via call to __getitem__ method) output pin of the underlying EP object
			"""
            return self._ep.add_sink(ep, output_name=self._output_name)

        def sink(self, ep):
            """Same as add_sink
			"""
            return self.add_sink(ep)

        def add_source(self, ep):
            """Adds the ep parameter as source to
			the selected(at construction or via call to input or __call__ methods) input pin of the underlying EP object
			"""
            return self._ep.add_source(ep, input_name=self._input_name)

        def source(self, ep):
            """Same as add_source
			"""
            return self.add_source(ep)

        def __rshift__(self, ep):
            """Same as add_sink
			"""
            return self.add_sink(ep)

        def __lshift__(self, ep):
            """Same as add_source
			"""
            return self.add_source(ep)

        def input(self, input_name):
            """Selects the input pin name
			"""
            self._input_name = input_name
            return self

        def __call__(self, input_name):
            """Same as input method
			"""
            return self.input(input_name)

        def __getitem__(self, output_name):
            """Selects the output pin name
			"""
            self._output_name = output_name
            return self

        def set_propagation_order_for_sink(self, ep, propagation_order):
            """
            Sets event propagation order for a particular sink of the underlying EP object,
			connected to the selected (at construction or via call to __getitem__ method) output pin of the underlying EP object.
			"""
            return self._ep.set_propagation_order_for_sink(ep, propagation_order, output_name=self._output_name)

        def copy(self, keep_indexes=False):
            cls = self.__class__
            new_copy = cls.__new__(cls)
            cls.__init__(new_copy, self._ep.copy(keep_indexes=keep_indexes))
            new_copy._output_name = _copy.copy(self._output_name)
            new_copy._input_name = _copy.copy(self._input_name)
            return new_copy

    nodeIndex = 1

    def __init__(self, name):
        self.name_ = name
        self.symbols_ = []
        self.tick_types_ = []
        self.process_node_locally_ = False
        self.node_name_ = ""
        self.output_data_ = False
        EpBase.nodeIndex = EpBase.nodeIndex + 1
        self.extra_parameters_ = {'node_index': 'NODE_{n}'.format(n=EpBase.nodeIndex)}
        self.sinks_ = []
        self.sources_ = []
        self.ep_outputs_ = {}
        self.input_pin_names_ = {}
        self.output_pin_names_ = {}

    def get_sinks(self):
        return self.sinks_

    def set_parameter(self, key, value):
        if key in self.__class__.Parameters.list_parameters():
            setattr(self, key, value)
        elif key.lower() in self.__class__.Parameters.list_parameters():
            setattr(self, key.lower(), value)
        elif key == "TICK_TYPE" and self._get_name() == "FIND_DB_SYMBOLS":
            setattr(self, "tick_type_field", value)
        else:
            self.extra_parameters_[key] = value
        return self

    def _get_symbol_strings(self):
        return self.symbols_

    def copy(self, keep_indexes=False):
        """Returns a copy of the event processor. No relations between nodes are copied(simply the parameters)"""
        cls = self.__class__
        new_copy = cls.__new__(cls)
        cls.__init__(new_copy)
        for param_label in cls.Parameters.list_parameters():
            param_value = getattr(self, param_label)
            setattr(new_copy, param_label, param_value)

        new_copy.symbols_ = _copy.copy(self.symbols_)
        new_copy.tick_types_ = _copy.copy(self.tick_types_)
        new_copy.process_node_locally_ = _copy.copy(self.process_node_locally_)
        new_copy.node_name_ = _copy.copy(self.node_name_)
        new_copy.output_data_ = _copy.copy(self.output_data_)
        new_copy.extra_parameters_ = _copy.copy(self.extra_parameters_)
        if not keep_indexes:
            EpBase.nodeIndex = EpBase.nodeIndex + 1
            new_copy.extra_parameters_['node_index'] = 'NODE_{n}'.format(n=EpBase.nodeIndex)
        new_copy.input_pin_names_ = _copy.deepcopy(self.input_pin_names_)
        new_copy.output_pin_names_ = _copy.deepcopy(self.output_pin_names_)
        return new_copy

    def set_symbol(self, symbol):
        """
        Sets symbol attached to this node and returns reference to current event processor

		Positional arguments:
		symbol (string) :
			Symbol for this node.

		Returns :
			Reference to current event processor.
		"""
        from .query import Query
        if isinstance(symbol, Query):
            self.symbols_ = 'eval({})'.format(symbol.unique_name)
        else:
            self.symbols_ = [symbol]
        return self

    def symbol(self, symbol):
        """Sets symbol attached to this node and returns reference to current event processor

		Positional arguments:
		symbol (string) :
			Symbol for this node.

		Returns :
			Reference to current event processor.
		"""
        return self.set_symbol(symbol)

    def set_symbols(self, symbols):
        """
        Sets symbols attached to this node and returns reference to current event processor

		Positional arguments:
		symbols (list of strings) :
			Symbols for this node

		Returns :
			Reference to current event processor.
		"""
        from .utils import SymbolResultMap, SymbolResultList
        from .query import GraphQuery
        import pandas as pd
        if isinstance(symbols, GraphQuery):
            self.symbols_ = 'eval({})'.format(symbols.unique_name)
        elif isinstance(symbols, SymbolResultMap) or isinstance(symbols, SymbolResultList):
            self.symbols_ = get_symbols_list_from_result(symbols)
        elif isinstance(symbols, str):
            if symbols.startswith("eval"):
                self.symbols_ = symbols
            else:
                self.symbols_ = 'eval({})'.format(symbols)
        elif isinstance(symbols, pd.DataFrame):
            self.symbols_ = get_symbols_from_pandas(symbols)
        else:
            self.symbols_ = symbols[:]
        return self

    def symbols(self, symbols=None):
        """
		1. Set symbols attached to this node if symbols parameter is passed(returns reference to current event
		processor for easy chaining of calls)
		1. Get symbols attached to this node if no symbols is passed.

		Positional arguments:
		symbols (list of strings, default: None(acts as a getter)) :
			Symbols for this node. Use empty list to clear the list of symbols attached to current node.

		Returns :
			1. Reference to current event processor if a parameter is passed.
			2. List of symbols attached to this node if no parameter is passed.

		Examples:
			1. Passthrough().symbols(["FULL_DEMO_L1:A", "FULL_DEMO_L1:AA"]) -> create a Passthrough bind FULL_DEMO_L1:A
			and FULL_DEMO_L1:AA symbols to it
			2. p=Passthrough()
			   print(p.symbols()) -> print list of symbols attached to this event processor
		"""
        if symbols is not None:
            return self.set_symbols(symbols)
        else:
            return self.symbols_

    def set_tick_type(self, tick_type):
        """
        Sets tick type attached to this node and returns reference to current event processor

		Positional arguments:
		tick_type (string) :
			Tick type for this node.

		Returns :
			Reference to current event processor.
		"""
        self.tick_types_ = [tick_type]
        return self

    def tick_type(self, tick_type):
        """
        Sets tick type attached to this node and returns reference to current event processor

		Positional arguments:
		tick_type (string) :
			Tick type for this node.

		Returns :
			Reference to current event processor.
		"""
        return self.set_tick_type(tick_type)

    def set_tick_types(self, tick_types):
        """
        Sets tick types attached to this node and returns reference to current event processor

		Positional arguments:
		tick_types (list of strings) :
			Tick types for this node.

		Returns :
			Reference to current event processor.
		"""
        self.tick_types_ = tick_types[:]
        return self

    def tick_types(self, tick_types=None):
        """
		1. Sets tick types attached to this node if tick_types parameter is passed returns reference to current event
		processor
		2. Gets tick types attached to this node if no tick_types parameter is passed.

		Keyword arguments:
		tick_types (list of strings, default: None(acts as a getter)) :
			Tick types for this node. Use empty list if you want to clear the list of tick types attached to this node.

		Returns :
			1. Reference to current event processor if a parameter is passed.
			2. List of tick types attached to this node if no parameter is passed.

		Examples:
			1. Passthrough().tick_types(["TRD", "QTE"]) -> create a Passthrough bind TRD and QTE tick types to it
			2. p=Passthrough()
			   print(p.tick_types()) -> print list of tick types attached to this event processor
		"""
        if tick_types is not None:
            return self.set_tick_types(tick_types)
        else:
            return self.tick_types_

    def set_output_data(self, tag):
        """Sets the name under which the node will output data(generally used for numpy queries)

		Positional arguments:
		tag (string):
			the name under which the node will output data, and also it's node_name.

		Returns :
			Reference to current event processor
		"""
        if not isinstance(tag, str):
            raise OneTickException('The tag parameter should be of type string', ErrorTypes.ERROR_INVALID_ARGUMENT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        self.node_name(tag, always_output_data=True)
        return self

    def output_data(self, tag=None):
        """
		The method is deprecated. The same result can be achieved via ep.node_name('...')
		1. If tag parameter is passed, makes the node to output data under output name tag(generally used for
		numpy queries)
		1. If the node doesn't output data returns None, otherwise returns the name of output.

		Keyword arguments:
		tag (string, default: None):
			Set the node_name of the EP and output data under this name.

		Returns :
			1. Reference to current event processor if a parameter is passed.
			2. The name of the output that the node will produce, None if the node does not produce output.

		Examples:
			1. Passthrough().output_data('OUTPUT_FROM_PASSTHROUGH') -> create a Passthrough, set it is node_name to
			'OUTPUT_FROM_PASSTHROUGH'

			and force it to return data
			2. p=Passthrough()
			   print(p.output_data()) -> see under what name p outputs data(will return None because p doesn't output data)
		"""
        if tag is not None:
            return self.set_output_data(tag)
        else:
            return self.node_name()

    def set_process_node_locally(self, process_node_locally):
        """Sets whether this node must be processed locally

		Positional arguments:
		process_node_locally(boolean, default: False) :
			True if current node must be processed locally and False otherwise.

		Returns :
			Reference to current event processor
		"""
        self.process_node_locally_ = process_node_locally
        return self

    def process_node_locally(self, process_node_locally=None):
        """
		1. Sets whether this node must be processed locally if process_node_locally parameter is
		passed(returns reference to current event processor for easy chaining of calls)
		1. Gets whether current event processor must be processed locally if no parameter is passed

		Keyword arguments:
		process_node_locally (boolean, default: None(acts as a getter)) :
			True if current node must be processed locally and False otherwise

		Returns :
			1. Reference to current event processor if process_node_locally is passed.
			2. Whether current event processor will be process locally if process_node_locally is not passed.

		Examples:
			1. Passthrough().process_node_locally(True) -> create a Passthrough event processor and force it to be
			processed locally
			2. p=Passthrough()
			   print(p.process_node_locally()) -> check whether or not current event processor will be processed locally
		"""
        if process_node_locally is not None:
            return self.set_process_node_locally(process_node_locally)
        else:
            return self.process_node_locally_

    def set_node_name(self, node_name, always_output_data=False):
        """
        Sets label for this node(Usage examples: some nodes may require its sources being labeled in order to be able to
        uniquely identify streams(e.g JOIN)).

		Positional arguments:
		node_name (string, default: empty) :
			Label for this node

		Returns :
			Reference to current event processor.
		"""
        self.output_data_ = always_output_data
        self.node_name_ = node_name
        return self

    def node_name(self, node_name=None, always_output_data=False):
        if node_name is not None:
            return self.set_node_name(node_name, always_output_data)
        else:
            return self.node_name_

    def input(self, input_name):
        """Select the input pin name on the EP
		(The returned object is a wrapper on the EP, which when sunk to other EPs will use the selected input pin).

		Positional arguments:
		input_name (String) :
			The name of the input pin

		Returns:
			PinnedEp object, which in most cases is same as EP.
		"""
        return self.PinnedEp(self, input_name=input_name)

    def __call__(self, input_name):
        """Same as input method"""
        return self.input(input_name)

    def __getitem__(self, output_name):
        """Select the output pin name on the EP
		(The returned object is a wrapper on the EP, which when sourced to other EPs will use the selected output pin).

		Positional arguments:
		output_name (String) :
			The name of the output pin

		Returns:
			PinnedEp object, which in most cases is same as EP.
		"""
        return self.PinnedEp(self, output_name=output_name)

    def add_sink(self, ep, output_name="", input_name=""):
        """Adds the passed event processor as a child of the current event processor
		(current event processor will feed its data to the event processor specified).

		Positional arguments:
		ep (EventProcessor) :
			Child event processor

		Keyword arguments:
		output_name (string, default: default output) :
			Specifies the output to which child node must be attached(e.g. IF branch of WHERE_CLAUSE)

		Returns :
			Reference to child event processor.
		"""
        if isinstance(ep, self.PinnedEp):
            self.add_sink(ep._ep, output_name=output_name, input_name=ep._input_name)
            return ep
        if isinstance(ep, Chainlet):
            self.add_sink(ep.first(), output_name)
            return ep
        for sink in self.sinks_:
            if sink._ep == ep and sink._output_name == output_name and sink._input_name == input_name:
                return ep
        self.sinks_.append(self.Sink(ep, output_name=output_name, input_name=input_name))
        ep.sources_.append(self.Source(self, output_name=output_name, input_name=input_name))
        return ep

    def sink(self, ep, output_name="", input_name=""):
        """Adds the passed event processor as a child of the current event processor
		(current event processor will feed its data to the event processor specified).

		Positional arguments:
		ep (EventProcessor) :
			Child event processor

		Keyword arguments:
		output_name (string, default: default output) :
			Specifies the output to which child node must be attached(e.g. IF branch of WHERE_CLAUSE)

		Returns :
			Reference to current event processor.
		"""
        return self.add_sink(ep, output_name, input_name)

    def __rshift__(self, ep):
        """Same as add_sink method
		"""
        return self.add_sink(ep)

    def add_source(self, ep, output_name="", input_name=""):
        """Adds the passed event processor as a source of the current event processor
		(current event processor will receive data from the event processor specified).

		Positional arguments:
		ep (EventProcessor or SymbolNumpyResultList):
			Source event processor or data object, which will become source of ticks for ep.

		Keyword arguments:
		output_name (string, default: default output) :
			Specifies the source event processor output through which current event processor will receive data(e.g. IF
			branch of WHERE_CLAUSE)

		Returns :
			Reference to source event processor or reference to current event processor, if the source is data object.
		"""
        if isinstance(ep, self.PinnedEp):
            self.add_source(ep._ep, output_name=ep._output_name, input_name=input_name)
            return ep
        for source in self.sources_:
            if source._ep == ep and source._output_name == output_name and source._input_name == input_name:
                return ep
        self.sources_.append(self.Source(ep, output_name=output_name, input_name=input_name))
        ep.sinks_.append(self.Sink(self, output_name=output_name, input_name=input_name))
        return ep

    def source(self, ep, output_name="", input_name=""):
        """Adds the passed event processor as a source of the current event processor
		(current event processor will receive data from the event processor specified).

		Positional arguments:
		ep (EventProcessor) :
			Source event processor.

		Keyword arguments:
		output_name (string, default: default output) :
			Specifies the source event processor output through which current event processor will receive data(e.g. IF
			branch of WHERE_CLAUSE)

		Returns :
			Reference to current event processor.
		"""
        return self.add_source(ep, output_name, input_name)

    def __lshift__(self, ep):
        """Same as add_source method
		"""
        return self.add_source(ep)

    def set_input_pin_name(self, pin_name, input_name=''):
        """Sets input pin name for specified input of this EP.

		Positional arguments:
		pin_name (string) :
			Input pin name for this EP

		Keyword arguments:
		input_name (string, default: '')
			If specified, pin_name will be added to specific input of the EP.

		Returns :
			Reference to current event processor.
		"""
        self.input_pin_names_[input_name] = pin_name
        return self

    def input_pin_name(self, pin_name=None, input_name=''):
        """
		1. Sets input pin name for this ep if pin_name parameter is passed.
		2. Gets input pin name of this ep for specified input name.

		Keyword arguments:
		pin_name (string, default: None) :
			Input pin name for this EP.
		input_name(string, default: '')
			Input name for this EP.
			If specified, it will set/get input pin name for specific input of this EP.

		Returns :
			1. Reference to current event processor if pin_name parameter is passed.
			2. Current event processor's input pin name for specified input if pin_name parameter is not passed.
		"""

        if pin_name is not None:
            return self.set_input_pin_name(pin_name, input_name)
        else:
            return self.input_pin_names_[input_name]

    def set_output_pin_name(self, pin_name, output_name=''):
        """Sets output pin name for specified output of this EP.

		Positional arguments:
		pin_name (string) :
			Output pin name for this EP

		Keyword arguments:
		output_name (string, default: '')
			If specified, pin_name will be added to specific output of the EP.

		Returns :
			Reference to current event processor.
		"""
        self.output_pin_names_[output_name] = pin_name
        return self

    def output_pin_name(self, pin_name=None, output_name=''):
        """
		1. Sets output pin name for this ep if pin_name parameter is passed.
		2. Gets output pin name of this ep for specified output name.

		Keyword arguments:
		pin_name (string, default: None) :
			Output pin name for this EP.
		output_name(string, default: '')
			Output name for this EP.
			If specified, it will set/get output pin name for specific output of this EP.

		Returns :
			1. Reference to current event processor if pin_name parameter is passed.
			2. Current event processor's output pin name for specified output if pin_name parameter is not passed.
		"""
        if pin_name is not None:
            return self.set_output_pin_name(pin_name, output_name)
        else:
            return self.output_pin_names_[output_name]

    def set_propagation_order_for_sink(self, ep, propagation_order, output_name="", input_name=""):
        """Sets event propagation order for a particular sink of the current event processor.

		Positional arguments:
		ep (EventProcessor) :
			Child event processor
		propagation_order (integer) :
			Event propagation order for the specified sink

		Keyword arguments:
		output_name (string, default: default output) :
			Specifies the output to which the sink node is attached(e.g. IF branch of WHERE_CLAUSE)
		input_name(string, default: '')
			Specifies the input pint name of the sink node to which current event processor is connected

		Returns :
			Reference to the current event processor.
		"""
        if isinstance(ep, self.PinnedEp):
            self.set_propagation_order_for_sink(ep._ep, propagation_order, output_name=output_name,
                                                input_name=ep._input_name)
            return ep
        if isinstance(ep, Chainlet):
            self.set_propagation_order_for_sink(ep.first(), propagation_order, output_name)
            return ep

        found = False
        for sink in self.sinks_:
            if (sink._ep == ep) and (sink._output_name == output_name) and (sink._input_name == input_name):
                sink.propagation_order_ = propagation_order
                found = True
        if not found:
            raise OneTickException('The specified event processor cannot be found among sinks of the current event '
                                   'processor.', ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        found = False
        for source in ep.sources_:
            if (source._ep == self) and (source._output_name == output_name) and (source._input_name == input_name):
                source.propagation_order_ = propagation_order
                found = True
        if not found:
            raise OneTickException('The specified event processor cannot be found among sinks of the current event '
                                   'processor.', ErrorTypes.ERROR_INVALID_GRAPH, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        return self


class Chainlet(object):
    """
	This class is designed for handling linear parts of graph construction more elegantly.
	A chainlet is simply a linear sequence of event processors within a graph(an alias for the sequence).

	E.g.
	left_branch=Chainlet(Passthrough(), AddField(field="IND", value="0"))
	right_branch=Chainlet(Passthrough(), AddField(field="IND", value="1"))
	graph=Graph(attach([left_branch, right_branch], JoinByTime())
	"""

    class ChainletOutput:
        def __init__(self, output_name, chainlet):
            self.ch_ = chainlet
            self._output_name = output_name

        def append(self, ep):
            return self.ch_.append(ep, self._output_name)

        def link(self, ep):
            return self.ch_.link(ep, self._output_name)

        def __rshift__(self, ep):
            return self.link(ep)

        def __iadd__(self, ext):
            return self.append(ext)

        def set_propagation_order_for_sink(self, ep, propagation_order):
            return self.ch_.set_propagation_order_for_sink(ep, propagation_order, self._output_name)

    def __init__(self, *eps):
        self.chain_ = []
        self.last_out_ = ''
        for ep in eps:
            self.append(ep)

    def last(self):
        """Returns the last event processor in the chainlet.

		Returns :
			Returns the last event processor in the chainlet.
		"""
        if len(self.chain_) == 0:
            raise OneTickException('the Chainlet is empty', ErrorTypes.ERROR_GENERIC,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return self.chain_[-1]

    def first(self):
        """Returns the first event processor in the chainlet.

		Returns :
			Returns the first event processor in the chainlet.
		"""
        if len(self.chain_) == 0:
            raise OneTickException('the Chainlet is empty', ErrorTypes.ERROR_GENERIC,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return self.chain_[0]

    def append(self, ext, output_name=''):
        """
		1. If ext is an event processor(or EpBase.PinnedEp) then that event processor is simply added to the current chainlet.
		2. If ext is a chainlet then the current chainlet is extended by the chainlet passed.
		Using append method is equivalent to using operator +=.

		Positional arguments :
		ext(EventProcessor or Chainlet)
			The extension for the current chainlet.

		Returns :
			1. Reference to the current chainlet.
		"""
        last_node = self.chain_[-1] if len(self.chain_) != 0 else None
        if last_node and isinstance(last_node, EpBase.PinnedEp):
            self.chain_.append(ext)
            last_node.add_sink(ext)
        else:
            if isinstance(ext, Chainlet):
                self.chain_.extend(ext.chain_)
                if len(ext.chain_) != 0 and last_node:
                    last_node.add_sink(ext.chain_[0], output_name)
            elif isinstance(ext, EpBase) or isinstance(ext, EpBase.PinnedEp):
                self.chain_.append(ext)
                if last_node:
                    last_node.add_sink(ext, output_name)
            else:
                raise OneTickException('Trying to add extension to the chainlet of type different from EventProcessor '
                                       'or Chainlet.', ErrorTypes.ERROR_INVALID_INPUT,
                                       getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)
        return self

    def link(self, ext, output_name=''):
        """The output of current chainlet is feed to the extension passed.
		Using link method is equivalent to using operator >>.

		Positional arguments :
		ext(EventProcessor or Chainlet)
			The extension for the current chainlet.

		Returns:
			Reference to ext.
		"""
        last_node = self.chain_[-1] if len(self.chain_) != 0 else None
        if not last_node:
            raise OneTickException("Trying to link empty chainlet's output to some part of the graph.",
                                   ErrorTypes.ERROR_INVALID_INPUT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        element_to_sink = ext
        if isinstance(ext, Chainlet):
            if len(ext.chain_) == 0:
                return ext
            element_to_sink = ext.chain_[0]
        if isinstance(last_node, EpBase.PinnedEp) and output_name != '':
            last_node[output_name].add_sink(element_to_sink)
        if isinstance(last_node, EpBase.PinnedEp) or isinstance(last_node, EpBase):
            last_node.add_sink(element_to_sink, output_name)
        return ext

    def __rshift__(self, ext):
        return self.link(ext)

    def __iadd__(self, ext):
        return self.append(ext)

    def __getitem__(self, output_name):
        return self.ChainletOutput(output_name, self)

    def __setitem__(self, output_name, ext):
        if ext == self:
            pass
        else:
            raise OneTickException('Chainlets are not supposed to handle any other syntax but ch[<output_name>] >> '
                                   '<component> or ch[<output_name>] += <component>', ErrorTypes.ERROR_INVALID_INPUT,
                                   getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

    def __iter__(self):
        return iter(self.chain_)

    def copy(self, keep_indexes=False):
        """Constructs and returns a deep copy of current chainlet.

		Returns :
			Reference a new chainlet
		"""
        chainlet_copy = Chainlet()
        orig_prev_ep = None
        new_prev_ep = None
        for ep in self.chain_:
            new_ep = ep.copy(keep_indexes=keep_indexes)
            chainlet_copy.chain_.append(new_ep)
            if orig_prev_ep:
                for sink in orig_prev_ep.sinks_:
                    if sink.ep == ep:
                        new_prev_ep.add_sink(new_ep, sink._output_name)
            orig_prev_ep = ep
            new_prev_ep = new_ep
        return chainlet_copy

    def set_propagation_order_for_sink(self, ext, propagation_order, output_name=''):
        """Sets event propagation order for the extension passed.

		Positional arguments :
		ext(EventProcessor or Chainlet)
			The extension for the current chainlet.
		propagation_order (integer) :
			Event propagation order for the specified link

		Returns:
			Reference to the current chainlet.
		"""
        last_node = self.chain_[-1] if len(self.chain_) != 0 else None
        if not last_node:
            raise OneTickException("Trying to set propagation order for the link link from an empty chainlet.",
                                   ErrorTypes.ERROR_INVALID_INPUT, getframeinfo(currentframe()).filename,
                                   getframeinfo(currentframe()).lineno)
        element_to_sink = ext
        if isinstance(ext, Chainlet):
            if len(ext.chain_) == 0:
                return ext
            element_to_sink = ext.chain_[0]
        if isinstance(last_node, EpBase.PinnedEp):
            last_node.set_propagation_order_for_sink(element_to_sink, propagation_order)
        else:
            last_node.set_propagation_order_for_sink(element_to_sink, propagation_order, output_name=output_name)
        return self
