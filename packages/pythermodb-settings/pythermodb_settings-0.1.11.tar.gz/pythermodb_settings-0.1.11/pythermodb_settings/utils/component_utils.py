# import libs
import logging
from typing import Literal
from pythermodb_settings.models import Component
# local
from ..models import ComponentIdentity

# NOTE: logger
logger = logging.getLogger(__name__)


def create_component_id(
    component: Component,
    separator_symbol: str = '-'
) -> ComponentIdentity:
    '''
    Create component name-state and formula-state identifiers.

    Parameters
    ----------
    component : Component
        The component for which to create the identifiers.
    separator_symbol : str, optional
        The symbol to use as a separator between the name/formula and

    Returns
    -------
    ComponentIdentity
        The component identity containing name-state and formula-state
        identifiers.
    '''
    try:
        # NOTE: extract component name
        component_name = component.name.strip()
        component_formula = component.formula.strip()
        component_state = component.state.strip().lower()

        # >> separator
        separator_symbol = separator_symbol.strip()

        # SECTION: create component identifiers
        name_state = f"{component_name}{separator_symbol}{component_state}"
        formula_state = f"{component_formula}{separator_symbol}{component_state}"

        return ComponentIdentity(
            name_state=name_state,
            formula_state=formula_state
        )
    except Exception as e:
        logger.error(
            f"Failed to create component identifiers for "
            f"'{component}': {e}"
        )
        raise e


def set_component_id(
    component: Component,
    component_key: Literal[
        'Name-State',
        'Formula-State',
        'Name',
        'Formula',
        'Name-Formula-State',
        'Formula-Name-State'
    ],
    separator_symbol: str = '-',
    case: Literal['lower', 'upper', None] = None
) -> str:
    '''
    Set component identifier based on the specified key.

    Parameters
    ----------
    component : Component
        The component for which to set the identifier.
    component_key : str
        The key to determine which identifier to use.
        Options are:
            - 'Name-State': Use the name-state identifier.
            - 'Formula-State': Use the formula-state identifier.
            - 'Name': Use the component name.
            - 'Formula': Use the component formula.
            - 'Name-Formula-State': Use the name, formula, and state.
            - 'Formula-Name-State': Use the formula, name, and state.
    separator_symbol : str, optional
        The symbol to use as a separator between the name/formula and state.
        Default is '-'.
    case : Literal['lower', 'upper', None], optional
        Convert the identifier to lower or upper case.

    Returns
    -------
    str
        The component identifier based on the specified key.
    '''
    try:
        # NOTE: create component id
        component_idx: ComponentIdentity = create_component_id(
            component=component,
            separator_symbol=separator_symbol
        )

        # init component id
        component_id: str = ""

        # NOTE: set component id
        if component_key == "Name-State":
            component_id = component_idx.name_state.strip()
        elif component_key == "Formula-State":
            component_id = component_idx.formula_state.strip()
        elif component_key == "Name":
            component_id = component.name.strip()
        elif component_key == "Formula":
            component_id = component.formula.strip()
        elif component_key == "Name-Formula-State":
            component_id = f"{component.name.strip()}{separator_symbol}{component.formula.strip()}{separator_symbol}{component.state.strip().lower()}"
        elif component_key == "Formula-Name-State":
            component_id = f"{component.formula.strip()}{separator_symbol}{component.name.strip()}{separator_symbol}{component.state.strip().lower()}"
        else:
            raise ValueError(
                f"Invalid component_key '{component_key}'. "
                f"Must be 'Name-State' or 'Formula-State'."
            )

        # NOTE: apply conversion
        if case == 'lower':
            component_id = component_id.lower()
        elif case == 'upper':
            component_id = component_id.upper()
        elif case is None:
            pass
        else:
            raise ValueError(
                f"Invalid case '{case}'. "
                f"Must be 'lower', 'upper', or None."
            )

        # result
        return component_id
    except Exception as e:
        logger.error(
            f"Failed to set component identifier for "
            f"'{component}': {e}"
        )
        raise e


def create_binary_mixture_id(
    component_1: Component,
    component_2: Component,
    mixture_key: Literal[
        'Name', 'Formula'
    ] = 'Name',
    delimiter: str = "|"
) -> str:
    """Create a unique binary mixture ID based on two components.

    Parameters
    ----------
    component1 : Component
        The first component in the mixture.
    component2 : Component
        The second component in the mixture.
    component_key : Literal['Name', 'Formula'], optional
        The key to use for identifying the components, by default 'Name'.
    delimiter : str, optional
        Delimiter to separate the two components in the ID, by default "|".

    Returns
    -------
    str
        A unique binary mixture ID.

    Raises
    ------
    ValueError
        If the component_key is not recognized.

    Examples
    --------
    The following example creates a binary mixture ID for water and ethanol
    using their names:

    >>> comp1 = Component(name="Water", formula="H2O", state="l")
    >>> comp2 = Component(name="Ethanol", formula="C2H5OH", state="l")
    >>> create_binary_mixture_id(comp1, comp2, mixture_key='Name')
    'Ethanol|Water'
    """
    try:
        # SECTION: validate inputs
        # NOTE: component
        if (
            not isinstance(component_1, Component) or
            not isinstance(component_2, Component)
        ):
            raise TypeError(
                "Both component1 and component2 must be instances of Component"
            )

        # NOTE: delimiter
        if not isinstance(delimiter, str):
            raise TypeError("delimiter must be a string")
        # strip delimiter
        delimiter = delimiter.strip()

        # SECTION: get component IDs
        if mixture_key == 'Name':
            comp1_id = component_1.name.strip()
            comp2_id = component_2.name.strip()
        elif mixture_key == 'Formula':
            comp1_id = component_1.formula.strip()
            comp2_id = component_2.formula.strip()
        else:
            raise ValueError(
                "component_key must be either 'Name' or 'Formula'"
            )

        # SECTION: create unique mixture ID (sorted to ensure uniqueness)
        mixture_id = delimiter.join(sorted([comp1_id, comp2_id]))
        # strip
        mixture_id = mixture_id.strip()

        # return
        return mixture_id
    except Exception as e:
        logging.error(f"Error in create_binary_mixture_id: {e}")
        raise


def create_mixture_id(
    components: list[Component],
    mixture_key: Literal[
        'Name',
        'Formula',
        'Name-State',
        'Formula-State',
        'Name-Formula-State',
        'Formula-Name-State'
    ] = 'Name',
    delimiter: str = "|",
    case: Literal['lower', 'upper', None] = None
) -> str:
    """Create a unique mixture ID based on a list of components (sorted alphabetically).

    Parameters
    ----------
    components : list[Component]
        List of components in the mixture.
    component_key : Literal['Name', 'Formula', 'Name-State', 'Formula-State', 'Name-Formula-State', 'Formula-Name-State'], optional
        The key to use for identifying the components, by default 'Name'.
    delimiter : str, optional
        Delimiter to separate the components in the ID, by default "|".
    case : Literal['lower', 'upper', None], optional
        Convert the identifier to lower or upper case, by default 'lower'.

    Returns
    -------
    str
        A unique mixture ID.

    Raises
    ------
    ValueError
        If the component_key is not recognized.

    Examples
    --------
    The following example creates a mixture ID for water, ethanol, and methanol
    using their names:

    >>> comp1 = Component(name="Water", formula="H2O", state="l")
    >>> comp2 = Component(name="Ethanol", formula="C2H5OH", state="l")
    >>> comp3 = Component(name="Methanol", formula="CH3OH", state="l")
    >>> create_mixture_id([comp1, comp2, comp3], mixture_key='Name')
    'Ethanol|Methanol|Water'
    """
    try:
        # SECTION: validate inputs
        # NOTE: components
        if not all(isinstance(comp, Component) for comp in components):
            raise TypeError(
                "All items in components must be instances of Component"
            )
        if len(components) == 0:
            raise ValueError("components list cannot be empty")

        # NOTE: delimiter
        if not isinstance(delimiter, str):
            raise TypeError("delimiter must be a string")
        # strip delimiter
        delimiter = delimiter.strip()

        # SECTION: get component IDs
        component_ids = []
        for comp in components:
            if mixture_key == 'Name':
                comp_id = comp.name.strip()
            elif mixture_key == 'Formula':
                comp_id = comp.formula.strip()
            elif mixture_key == 'Name-State':
                comp_id = f"{comp.name.strip()}-{comp.state.strip()}"
            elif mixture_key == 'Formula-State':
                comp_id = f"{comp.formula.strip()}-{comp.state.strip()}"
            elif mixture_key == 'Name-Formula-State':
                comp_id = f"{comp.name.strip()}-{comp.formula.strip()}-{comp.state.strip()}"
            elif mixture_key == 'Formula-Name-State':
                comp_id = f"{comp.formula.strip()}-{comp.name.strip()}-{comp.state.strip()}"
            else:
                raise ValueError(
                    "component_key must be one of the following: Name, Formula, Name-State, Formula-State, Name-Formula-State, Formula-Name-State"
                )
            component_ids.append(comp_id)

        # SECTION: create unique mixture ID (sorted to ensure uniqueness)
        # ! sorted alphabetically
        mixture_id = delimiter.join(sorted(component_ids))

        # strip
        mixture_id = mixture_id.strip()

        # NOTE: apply conversion
        if case == 'lower':
            mixture_id = mixture_id.lower()
        elif case == 'upper':
            mixture_id = mixture_id.upper()
        elif case is None:
            pass

        # return
        return mixture_id
    except Exception as e:
        logging.error(f"Error in create_mixture_id: {e}")
        raise
