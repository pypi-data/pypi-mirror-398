# import libs
from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)
# local
from .components import Component


class ComponentThermoDBSource(BaseModel):
    '''
    ThermoDB source containing `component` thermodb.

    Attributes
    ----------
    component: Component
        Component thermodb
    source: str
        Path to the thermodb file
    '''
    component: Component = Field(
        ..., description="Component object containing name, formula, and state"
    )
    source: str = Field(
        ...,
        description="Path to the thermodb file"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow"
    )


class MixtureThermoDBSource(BaseModel):
    '''
    ThermoDB source containing `mixture` thermodb.

    Attributes
    ----------
    components: list[Component]
        List of components in the mixture thermodb
    source: str
        Path to the thermodb file
    '''
    components: list[Component] = Field(
        ...,
        description="List of components in the mixture thermodb"
    )
    source: str = Field(
        ...,
        description="Path to the thermodb file"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow"
    )
