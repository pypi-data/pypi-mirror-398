# import libs
from typing_extensions import TypedDict


class ComponentConfig(TypedDict, total=False):
    """
    Component configuration model

    Attributes
    ----------
    databook : str
        Name of the databook.
    table : str
        Name of the table in the databook.
    mode : str
        Mode of the configuration, e.g., 'strict', 'lenient'.
    label : str
        Optional label for the configuration.
    labels : dict[str, str]
        Optional dictionary of labels for additional configuration details.
    """
    databook: str
    table: str
    mode: str
    label: str  # optional
    labels: dict[str, str]  # optional
