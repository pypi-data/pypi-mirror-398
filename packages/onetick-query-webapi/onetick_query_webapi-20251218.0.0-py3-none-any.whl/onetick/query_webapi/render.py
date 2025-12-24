from .exception import *
from inspect import getframeinfo, currentframe


def render(query, file_path=None, img_format="svg", render_in_jupiter=True, view=True, verbose=False):
    """
	Renders the query to file and optionally displays it.
	If no file_path is specified then the rendered result is saved in the system tmp dir.
	If view is set to False then the rendered result will not be displayed.

	Positional arguments:
	query (OtqQuery, GraphQuery or ChainQuery) :
		The query to render.

	Keyword arguments:
	file_path (string, default: None(save in tmp dir)) :
		File path for storing rendered result.
	img_format (string, default: svg) :
		Format for storing rendered result(svg, pdf, png etc.).
	view (boolean, default: True) :
		Display the rendered result.
	verbose (boolean, default: False) :
		Display all information of EPs.
	render_in_jupiter (boolean, default: True):
		Defines weather or not the graph renders in jupyter (ignored if you are not in jupyter)
	"""
    from .query import GraphQuery, ChainQuery
    if not isinstance(query, GraphQuery) and not isinstance(query, ChainQuery):
        raise OneTickException("render methods expects either OtqQuery, GraphQuery or ChainQuery.",
                               ErrorTypes.ERROR_INVALID_ARGUMENT, getframeinfo(currentframe()).filename,
                               getframeinfo(currentframe()).lineno)
    query.render(file_path=file_path, img_format=img_format, render_in_jupiter=render_in_jupiter, view=view,
                 verbose=verbose)
