from enum import Enum
import string


def indent(n):
    return '\t' * n


def print_line(out, line, _indent=0):
    out.write(indent(_indent) + line + '\n')


def print_multi_line_string_with_indent(out, lines, _indent=0):
    for line in lines.split('\n'):
        print_line(out, line, _indent)


class ParamInfo:
    class ParamType(Enum):
        PARAM_TYPE_BOOLEAN = 1
        PARAM_TYPE_INTEGER = 2
        PARAM_TYPE_DOUBLE = 3
        PARAM_TYPE_STRING = 4
        PARAM_TYPE_ENUM = 5

        PARAM_TYPE_UNKNOWN = -1

    def __init__(self, name: str, value_type: ParamType, default_value, choices):
        self.name = name
        self.value_type = value_type
        self.default_value = default_value
        self.choices = choices


class EpInfo:
    def __init__(self, name: str, params: list):
        self.name = name
        self.params = params
        self.documentation = ""


def to_camel_case(raw_name):
    raw_name = raw_name.strip().lower()
    class_name = ""
    upper_case_flag = True
    for c in raw_name:
        if upper_case_flag:
            class_name = class_name + c.upper()
            upper_case_flag = False
        elif c == '_' or c == '/':
            upper_case_flag = True
        else:
            class_name = class_name + c
    class_name = class_name.replace("::", "_")
    class_name = class_name.replace(".otq", "Otq")
    class_name = class_name.replace(".", "_")
    return class_name


def get_ep_class_name(ep_info: EpInfo):
    have_postfix = False
    ep_class_name = ep_info.name
    for param in ep_info.params:
        if ep_class_name == param.name.upper():
            ep_class_name += "_EP"
            have_postfix = True
            break
    return to_camel_case(ep_class_name), have_postfix


def get_reserved_param_names():
    return {
        "NODE", "SINK", "SOURCE", "PINNEDEP", "SOURCE", "SET_PARAMETER", "COPY", "SYMBOL", "SET_SYMBOL", "SYMBOLS",
        "SET_SYMBOLS", "SET_TICK_TYPE", "TICK_TYPE", "SET_TICK_TYPES", "TICK_TYPES", "SET_CALLBACK", "CALLBACK",
        "SET_OUTPUT_DATA", "SET_PROCESS_NODE_LOCALLY", "PROCESS_NODE_LOCALLY", "SET_NODE_NAME", "NODE_NAME", "INPUT",
        "ADD_SINK", "ADD_SOURCE"
    }


def get_reserved_param_suffix():
    return "_FIELD"


def replace_special_chars_with_readable_words(enum_field: str):
    result = ""
    for ch in enum_field:
        if ch == '+':
            result += "_PLUS_"
        elif ch == '&':
            result += "_AND_"
        elif ch == '|':
            result += "_OR_"
        elif ch == '~':
            result += "_TILDA_"
        elif ch == '$':
            result += "_DOLLAR_"
        elif ch == '=':
            result += "_EQUAL_"
        elif ch == '%':
            result += "_PERCENT_"
        elif ch == '#':
            result += "_HASH_"
        elif ch == '-' or ch == ' ' or ch == '(' or ch == ')' or ch == '.' or ch == '/' or ch == '\\':
            result += "_"
        else:
            result += ch
    return result


def get_param_pythonic_name(param_name: str):
    param_python_name = param_name
    reserved_param_names = get_reserved_param_names()
    reserved_param_suffix = get_reserved_param_suffix()
    if param_name in reserved_param_names:
        param_python_name += reserved_param_suffix
    return replace_special_chars_with_readable_words(param_python_name).lower()


def escape_quotes(param):
    result = ""
    for ch in param:
        if ch == '"':
            result += "\\"
        result += ch
    return result


def html2text(html):
    def ispunct(ch):
        return ch in string.punctuation

    if html.find("<div id=\"Ref\">") != -1:
        html = html[:html.find("<div id=\"Ref\">")]
    if html.find("<p class=\"confidential\">") != -1:
        html = html[:html.find("<p class=\"confidential\">")]
    if html.find("<body>") != -1:
        html = html[html.find("<body>"):]

    open_brackets = 0
    index = 0
    text = ""
    current_tag = ""
    character_code = ["mdash"]
    character = ["-"]
    while index < len(html):
        if not (ispunct(html[index]) or html[index].isspace() or html[index].isdigit() or html[index].isalpha()):
            index += 1
            continue
        if html[index] == '&':
            found = False
            i = 0
            while i < len(character_code):
                if index + len(character_code[i]) < len(html):
                    if html[index+1:index+1+len(character_code[i])] == character_code[i]:
                        text += character[i]
                        index += len(character_code[i]) + 2
                        found = True
                        break
                i += 1
            if found:
                continue
        if html[index] == '<':
            open_brackets += 1
            current_tag += html[index]
        elif html[index] == '>':
            open_brackets -= 1
            current_tag += html[index]
            if current_tag == "</p>":
                text += "\n"
            current_tag = ""
        elif open_brackets == 0:
            if html[index] == '\\':
                text += '\\'
            if html[index] == '\r' or html[index] == '\n':
                text += "\n"
                while index < len(html) and (html[index] == '\r' or html[index] == '\n'):
                    index += 1
                index -= 1
            else:
                text += html[index]
        else:
            current_tag += html[index]
        index += 1
    return text
