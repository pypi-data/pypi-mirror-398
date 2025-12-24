"""
Stores general configuration parameters for extended python API.
SHOW_STACK_INFO       - if it is set to 1, then exceptions also contain code location where harmful EP was created.
SHOW_STACK_WARNING    - when it is set to 1 and SHOW_STACK_INFO=0, then we print a message in exceptions, that hints you
 						to enable SHOW_STACK_INFO option for more informative exceptions about stack.
RENDER_GRAPH_ON_ERROR - if query exits with an exception we will render the graph and mention the harmful EP by coloring
                        if the option is set to 1.
ENABLE_CODE_FLOW_LOGS - if set to 1, in case of query_webapi OAuth2 code flow authentication we will print some logs for
                        debug purposes
"""

API_CONFIG = {
    "SHOW_STACK_INFO": 0,
    "SHOW_STACK_WARNING": 1,
    "RENDER_GRAPH_ON_ERROR": 0,
    "ENABLE_CODE_FLOW_LOGS": 0,
    "ENABLE_DEBUG_LOGS": 0
}
