from os import path
from typing import Optional, List, Union


def py2sp_conditional(conditional: str) -> str:
    """
    Convert a Python conditional expression to SharePoint OData query syntax.

    Parameters
    ----------
    conditional : str
        A conditional expression using Python comparison operators.

    Returns
    -------
    str
        The expression with operators replaced by their OData equivalents.
    """
    return conditional.replace('==', 'eq').replace('!=', 'ne').replace('>=', 'ge').replace('<=', 'le').replace('>', 'gt').replace('<', 'lt')


def build_query_url(
    base_url: str,
    filters: Optional[Union[str, List[str]]] = None,
    select_fields: Optional[Union[str, List[str]]] = None,
    top: Optional[int] = None,
) -> str:
    """
    Construct a SharePoint OData query URL with optional filters, selected fields, and pagination.

    Parameters
    ----------
    base_url : str
        The base endpoint URL.
    filters : str or List[str], optional
        OData filter expression(s). If a list is provided, conditions are combined with ``and``.
    select_fields : str or List[str], optional
        Fields to include in the response via the ``$select`` query option.
    top : int, optional
        Maximum number of results to return. Defaults to 1000 if not specified.

    Returns
    -------
    str
        The fully constructed URL with query parameters.
    """
    # Build query arguments
    arguments = []

    if filters is not None:
        if not isinstance(filters, list):
            filter_string = py2sp_conditional(filters)
        else:
            filter_string = py2sp_conditional(' and '.join(filters))
        arguments.append(f'$filter={filter_string}')

    if select_fields is not None:
        if isinstance(select_fields, list):
            select_string = ','.join(select_fields)
        else:
            select_string = str(select_fields)
        arguments.append(f'$select={select_string}')

    if top is not None:
        arguments.append(f"$top={top}")
    # Construct final URL
    if arguments:
        return f'{base_url}?{"&".join(arguments)}'
    return base_url
