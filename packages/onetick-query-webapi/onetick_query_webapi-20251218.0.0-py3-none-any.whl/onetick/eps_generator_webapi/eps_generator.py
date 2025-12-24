import onetick.query_webapi as otq
import os
import tempfile
from .utils import *
from . import plugin


def generate_ep_infos(eps_list_otq, eps_documentation_otq, http_address, generate_documentation,
                      http_username, http_password, access_token, namespace):
    def is_number(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def is_boolean_param(type_name, default_value, choices, param_name):
        if param_name == "GO_BACK_TO_FIRST_TICK":
            return False
        if type_name.upper() == "BOOL" and (len(choices) == 2 or len(choices) == 0):
            return True
        is_boolean = (default_value and default_value.lower() in ['true', 'false']) or len(choices) > 0
        if is_boolean:
            for choice in choices:
                if choice.lower() not in ['true', 'false']:
                    return False
        return is_boolean

    def is_integer_param(type_name, default_value, choices):
        if type_name.upper() == "INTEGER" or type_name.upper() == "LONG":
            return True
        is_integer = default_value and is_number(default_value)
        if is_integer:
            for choice in choices:
                if not is_number(choice):
                    return False
        return is_integer

    def is_enum_param(type_name, default_value, choices, param_name):
        if type_name.upper() == "ENUM" and len(choices) > 1:
            return True
        if default_value and default_value not in choices:
            return False
        is_enum = len(choices) > 1 and not (is_boolean_param(type_name, default_value, choices, param_name) or
                                            is_integer_param(type_name, default_value, choices))
        return is_enum

    def detect_param_type(type_name, default_value, choices, param_name):
        choices = list(filter(None, choices))
        if is_boolean_param(type_name, default_value, choices, param_name):
            return ParamInfo.ParamType.PARAM_TYPE_BOOLEAN
        if is_integer_param(type_name, default_value, choices):
            return ParamInfo.ParamType.PARAM_TYPE_INTEGER
        if is_enum_param(type_name, default_value, choices, param_name):
            return ParamInfo.ParamType.PARAM_TYPE_ENUM
        return ParamInfo.ParamType.PARAM_TYPE_STRING

    def create_param_info(ep_name_param, param_name, value_type, default_value, choices):
        special_ep_params = [("FIND_DB_SYMBOLS", "CEP_METHOD"),
                             ("OM/STRATEGY_DB_MANAGER", "PERMISSION")]
        if (ep_name_param, param_name) in special_ep_params:
            choices.insert(0, "EMPTY")
            default_value = "EMPTY"
        return ParamInfo(param_name,
                         detect_param_type(value_type, default_value, choices, param_name),
                         default_value,
                         choices)

    data = otq.run(eps_list_otq, http_address, http_username=http_username, http_password=http_password,
                   access_token=access_token)["LOCAL::"]
    ep_infos = dict()
    cur_ep_info = EpInfo("", [])
    for idx, ep_name in enumerate(data['MY_EVENT_PROCESSOR_NAME']):
        ep_name = ep_name
        if namespace and not ep_name.startswith(namespace):
            continue
        if ep_name == cur_ep_info.name:
            if data['MY_PARAMETER_NAME'][idx]:
                cur_ep_info.params.append(
                    create_param_info(ep_name,
                                      data['MY_PARAMETER_NAME'][idx],
                                      data['MY_TYPE_EXPR'][idx],
                                      data['MY_PARAMETER_DEFAULT_VALUE'][idx],
                                      data['MY_PARAMETER_CHOICES'][idx].split(',')))
        else:
            cur_ep_info = EpInfo(ep_name, [])
            if data['MY_PARAMETER_NAME'][idx]:
                cur_ep_info.params.append(
                    create_param_info(ep_name,
                                      data['MY_PARAMETER_NAME'][idx],
                                      data['MY_TYPE_EXPR'][idx],
                                      data['MY_PARAMETER_DEFAULT_VALUE'][idx],
                                      data['MY_PARAMETER_CHOICES'][idx].split(',')))
            ep_infos[ep_name] = cur_ep_info

    if generate_documentation:
        data = otq.run(eps_documentation_otq, http_address, http_username=http_username, http_password=http_password,
                       access_token=access_token, compression="none")["LOCAL::"]
        for idx, ep_name in enumerate(data['MY_EVENT_PROCESSOR_NAME']):
            if ep_name not in ep_infos:
                continue
            ep_infos[ep_name].documentation = str(data['MY_DOCUMENTATION'][idx])
    return ep_infos


def generate_ep_module(ep_infos, generate_documentation, plugin_name, output_dir):
    temp_dir = ""
    if plugin_name:
        temp_dir = tempfile.mkdtemp()
        plugin_dir = temp_dir + "/onetick/query_webapi/plugin/" + plugin_name
        os.makedirs(plugin_dir + "/ep")
        with open(plugin_dir + "/__init__.py", "w") as f:
            f.write('from .ep import *\n')
    else:
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        plugin_dir = cur_dir + "/../query_webapi"

    with open(plugin_dir + "/ep/__init__.py", "w") as f:
        f.write('from .eps import *\n')

    out = open(plugin_dir + "/ep/eps.py", "w")
    if plugin_name:
        print_line(out, 'import onetick.query_webapi.graph_components as _graph_components')
        print_line(out, 'import onetick.query_webapi._internal_utils as _internal_utils')
        print_line(out, 'import onetick.query_webapi.config as _config')
    else:
        print_line(out, 'from .. import graph_components as _graph_components')
        print_line(out, 'from .. import _internal_utils')
        print_line(out, 'from .. import config as _config')
        print_line(out, 'from .. import utils as _utils')
    print_line(out, '')
    print_line(out, '')
    for ep_name in ep_infos:
        generate_ep_class(ep_infos[ep_name], out, generate_documentation)
    out.close()

    out = open(plugin_dir + "/_eps_factory.py", "w")
    _indent = 0
    if not plugin_name:
        print_line(out, 'from . import eps_dict')
    print_line(out, 'from . import ep')
    print_line(out, 'from inspect import getframeinfo, currentframe')
    print_line(out, "")
    print_line(out, "")
    print_line(out, "def create_ep(ep_name):")
    for ep_name in ep_infos:
        print_line(out, "if ep_name == '" + ep_name + "':", _indent + 1)
        print_line(out, "return ep." + to_camel_case(ep_infos[ep_name].name) + "()", _indent + 2)
    if not plugin_name:
        print_line(out, "if ep_name in eps_dict:", _indent + 1)
        print_line(out, "return eps_dict[ep_name]()", _indent + 2)
    print_line(out, "")
    print_line(out,
               "raise Exception('wrong ep name: {}.'.format(ep_name), getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)",
               _indent + 1)
    out.close()
    if plugin_name:
        plugin.build(temp_dir, output_dir, plugin_name)


def generate_ep_class(ep_info: EpInfo, out, generate_documentation, _indent=0):
    ep_class_name, have_postfix = get_ep_class_name(ep_info)
    print_line(out, "class " + ep_class_name + "(_graph_components.EpBase):", _indent)
    if generate_documentation:
        print_line(out, "\"\"\"", _indent + 1)
        print_line(out, html2text(ep_info.documentation), _indent + 2)
        print_line(out, "\"\"\"", _indent + 1)
    generate_available_parameters_aliases(ep_info.params, out, _indent + 1)
    generate_enum_params_choices_wrapper_classes(ep_info.params, out, _indent + 1)
    generate_ep_constructor(ep_info, out, _indent + 1)
    generate_parameter_setters(ep_info.params, out, _indent + 1)
    generate_ep_to_string(ep_info, out, _indent + 1)
    generate_ep_destructor(out, _indent + 1)
    if have_postfix:
        print_line(out, "", _indent)
        print_line(out, to_camel_case(ep_info.name) + " = " + ep_class_name, _indent)
        print_line(out, "", _indent)

    special_ep_aliases = dict(
        [("NumTicks", "Count"), ("High", "Max"), ("Low", "Min"), ("Vwap", "WAvg"), ("Average", "Avg")]
    )
    if ep_class_name in special_ep_aliases:
        print_line(out, "", _indent)
        print_line(out, special_ep_aliases[ep_class_name] + " = " + ep_class_name, _indent)
        print_line(out, "", _indent)
    print_line(out, "")


def generate_available_parameters_aliases(ep_params, out, _indent):
    print_line(out, "class Parameters:", _indent)
    params_name_list = "["
    params_name_list_with_private_members = "["
    last_param_name = ""
    if ep_params:
        last_param_name = ep_params[-1].name
    for ep_param in ep_params:
        param_field_name = get_param_pythonic_name(ep_param.name)
        param_server_name = ep_param.name

        print_line(out, param_field_name + " = \"" + param_server_name + "\"", _indent + 1)
        params_name_list += "\"" + param_field_name + "\""
        params_name_list_with_private_members += "\"" + param_field_name + "\", "
        params_name_list_with_private_members += "\"_default_" + param_field_name + "\""
        if ep_param.name != last_param_name:
            params_name_list += ", "
            params_name_list_with_private_members += ", "

    print_line(out, "stack_info = \"STACK_INFO\"", _indent + 1)
    parameters_name_list_with_stack_info = params_name_list_with_private_members
    if ep_params:
        parameters_name_list_with_stack_info += ", "
    parameters_name_list_with_stack_info += "\"stack_info\", \"_used_strings\"]"

    # Construct list_parameters() method
    params_name_list += ']'
    print_line(out, "")
    print_multi_line_string_with_indent(
        out,
        "@staticmethod\n" +
        "def list_parameters():",
        _indent + 1)
    print_line(out, "list_val = " + params_name_list, _indent + 2)
    print_multi_line_string_with_indent(
        out,
        "if _config.API_CONFIG[\'SHOW_STACK_INFO\'] == 1:\n" +
        "	list_val.append(\"stack_info\")\n" +
        "return list_val",
        _indent + 2)
    print_line(out, "")
    print_line(out, "__slots__ = " + parameters_name_list_with_stack_info, _indent)
    print_line(out, "")


def generate_enum_params_choices_wrapper_classes(ep_params, out, _indent):
    for ep_param in ep_params:
        if ep_param.value_type == ParamInfo.ParamType.PARAM_TYPE_ENUM:
            generate_enum_choices_wrapper_class(ep_param, out, _indent)


def generate_enum_choices_wrapper_class(ep_param: ParamInfo, out, _indent):
    choices = ep_param.choices
    param_wrapper_class_name = to_camel_case(ep_param.name)

    print_line(out, "class " + param_wrapper_class_name + ":", _indent)
    if len(ep_param.default_value) == 0:
        print_line(out, "EMPTY = \"\"", _indent + 1)
    for choice in choices:
        if len(choice) == 0:
            continue
        choice_name = replace_special_chars_with_readable_words(choice).upper()
        if choice_name == "EMPTY":
            print_line(out, "EMPTY = \"\"", _indent + 1)
        else:
            print_line(out, choice_name + " = \"" + choice + "\"", _indent + 1)
    print_line(out, "")


def generate_ep_constructor(ep_info: EpInfo, out, _indent):
    is_in = False
    is_out = False
    class_name_line = "def __init__(self"
    for ep_param in ep_info.params:
        param_default = get_param_pythonic_default_value(ep_param)
        param_name = get_param_pythonic_name(ep_param.name)
        class_name_line += ", " + param_name + "=" + param_default
        if param_name == "input_field_name":
            is_in = True
        if param_name == "output_field_name":
            is_out = True
    if is_in:
        class_name_line += ", In = \"\""
    if is_out:
        class_name_line += ", Out = \"\""
    class_name_line += "):"
    print_line(out, class_name_line, _indent)

    print_line(out, "_graph_components.EpBase.__init__(self, \"" + ep_info.name + "\")", _indent + 1)
    for ep_param in ep_info.params:
        ep_pythonic_param_name = get_param_pythonic_name(ep_param.name)
        param_default = get_param_pythonic_default_value(ep_param, True)
        print_multi_line_string_with_indent(
            out,
            "self._default_" + ep_pythonic_param_name + " = " + param_default + "\n" +
            "self." + ep_pythonic_param_name + " = " + ep_pythonic_param_name,
            _indent + 1)

    if is_in:
        print_multi_line_string_with_indent(
            out,
            "if In != \"\":\n" +
            "	self.input_field_name=In",
            _indent + 1)
    if is_out:
        print_multi_line_string_with_indent(
            out,
            "if Out != \"\":\n" +
            "	self.output_field_name=Out",
            _indent + 1)
    print_multi_line_string_with_indent(
        out,
        "self._used_strings = {}\n" +
        "for param_name in type(self).__dict__:\n" +
        "	param_val = getattr(self, param_name, '')\n" +
        "	if isinstance(param_val, str) and _internal_utils.get_reference_counted_prefix() in param_val and not (param_val in self._used_strings):\n" +
        "		_internal_utils.inc_ref_count(param_val)\n" +
        "		self._used_strings[param_val] = 1",
        _indent + 1)
    # Retrieve caller filename and line number in python
    print_line(out, "import sys", _indent + 1)
    print_line(out, "frame = sys._getframe(1)", _indent + 1)
    print_line(out, "self.stack_info = frame.f_code.co_filename + \":\" + str(frame.f_lineno)", _indent + 1)
    print_line(out, "")


def get_param_pythonic_default_value(ep_param: ParamInfo, prepend_class_name: bool = False):
    param_default_value = ep_param.default_value
    if ep_param.value_type == ParamInfo.ParamType.PARAM_TYPE_STRING:
        return "\"" + escape_quotes(param_default_value) + "\""
    elif ep_param.value_type == ParamInfo.ParamType.PARAM_TYPE_BOOLEAN:
        if param_default_value.lower() == "true":
            return "True"
        else:
            return "False"
    elif ep_param.value_type == ParamInfo.ParamType.PARAM_TYPE_ENUM:
        choices_wrapper_class_name = to_camel_case(ep_param.name)
        choice_name = "EMPTY" if len(param_default_value) == 0 \
            else replace_special_chars_with_readable_words(param_default_value).upper()
        pref = "type(self)." if prepend_class_name else ""
        return pref + choices_wrapper_class_name + "." + choice_name
    if not param_default_value:
        return "\"\""
    return param_default_value


def generate_parameter_setters(ep_params, out, _indent):
    for ep_param in ep_params:
        param_name = get_param_pythonic_name(ep_param.name)
        print_line(out, "def set_" + param_name + "(self, value):", _indent)
        print_line(out, "self." + param_name + " = value", _indent + 1)
        print_line(out, "return self", _indent + 1)
        print_line(out, "")


def generate_ep_to_string(ep_info: EpInfo, out, _indent):
    ep_name = ep_info.name
    print_line(out, "@staticmethod", _indent)
    print_line(out, "def _get_name():", _indent)
    print_line(out, "return \"" + ep_name + "\"\n", _indent + 1)

    print_line(out, "def _to_string(self, for_repr=False):", _indent)
    print_line(out, "name = self._get_name()", _indent + 1)
    print_line(out, "desc = name + \"(\"", _indent + 1)
    print_line(out, "py_to_str = _utils.onetick_repr if for_repr else str", _indent + 1)

    for param in ep_info.params:
        pythonic_param_default = get_param_pythonic_default_value(param)
        pythonic_param_name = get_param_pythonic_name(param.name)
        pythonic_param_name_upper = pythonic_param_name.upper()

        if pythonic_param_name_upper == "TICK_TYPE_FIELD" and ep_name == "FIND_DB_SYMBOLS":
            pythonic_param_name_upper = "TICK_TYPE"
        needed_self = ""
        if param.value_type == ParamInfo.ParamType.PARAM_TYPE_ENUM:
            needed_self = "self."

        print_line(out, "if self." + pythonic_param_name + " != " + needed_self + pythonic_param_default + ": ",
                   _indent + 1)
        print_line(out, "desc += \"" + pythonic_param_name_upper + "=\" + py_to_str(self." + pythonic_param_name +
                   ") + \",\"", _indent + 2)
    print_line(out, "if _config.API_CONFIG[\'SHOW_STACK_INFO\'] == 1:", _indent + 1)
    print_line(out, "desc += \"STACK_INFO=\" + py_to_str(self.stack_info) + \",\"", _indent + 2)
    print_line(out, "desc = desc[:-1]", _indent + 1)
    print_line(out, "if desc != name:", _indent + 1)
    print_line(out, "desc += \")\"", _indent + 2)
    print_line(out, "if for_repr:", _indent + 1)
    print_line(out, "return desc + '()' if desc == name else desc", _indent + 2)
    print_line(out, "desc += \"\\n\"", _indent + 1)
    print_multi_line_string_with_indent(
        out,
        "if len(self._get_symbol_strings()) > 0:\n" +
        "	desc += \"SYMBOLS=[\" + \", \".join(self._get_symbol_strings()) + \"]\\n\"\n" +
        "if len(self.tick_types_) > 0:\n" +
        "	desc += \"TICK_TYPES=[\" + \', \'.join(self.tick_types_) + \"]\\n\"\n" +
        "if self.process_node_locally_:\n" +
        "	desc += \"PROCESS_NODE_LOCALLY=True\\n\"\n" +
        "if self.node_name_ != \"\":\n" +
        "	desc += \"NODE_NAME=\" + self.node_name_ + \"\\n\"\n" +
        "return desc",
        _indent + 1)
    print_multi_line_string_with_indent(
        out,
        "\n" +
        "def __repr__(self):\n" +
        "	return self._to_string(for_repr=True)\n" +
        "\n" +
        "def __str__(self):\n" +
        "	return self._to_string()",
        _indent)
    print_line(out, "")


def generate_ep_destructor(out, _indent):
    print_multi_line_string_with_indent(
        out,
        "def __del__(self):\n" +
        "	for param_name in getattr(self, '_used_strings', []):\n" +
        "		_internal_utils.dec_ref_count(param_name)\n" +
        "		if _internal_utils.get_ref_count(param_name) == 0:\n" +
        "			_internal_utils.remove_from_memory(param_name)",
        _indent)
    print_line(out, "")


def generate_plugin(plugin_name, output_dir, http_address, http_username=None, http_password=None, access_token=None,
                    generate_documentation=True, namespace=None):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    generate_ep_module(
        generate_ep_infos(cur_dir + "/eps_list.otq",
                          cur_dir + "/eps_list_doc.otq",
                          http_address,
                          generate_documentation,
                          http_username,
                          http_password,
                          access_token,
                          namespace),
        generate_documentation,
        plugin_name,
        output_dir)
