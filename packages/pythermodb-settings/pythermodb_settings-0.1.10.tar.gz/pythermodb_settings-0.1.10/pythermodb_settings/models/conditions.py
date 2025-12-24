# import libs
from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)


class Temperature(BaseModel):
    """
    Temperature model for input validation

    Attributes
    ----------
    value : float
        Temperature value.
    unit : str
        Temperature unit, e.g., 'K', 'C', 'F'.
    """
    value: float = Field(..., description="Temperature value")
    unit: str = Field(..., description="Temperature unit, e.g., 'K', 'C', 'F'")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow"
    )


class Pressure(BaseModel):
    """
    Pressure model for input validation

    Attributes
    ----------
    value : float
        Pressure value.
    unit : str
        Pressure unit, e.g., 'bar', 'atm', 'Pa'.
    """
    value: float = Field(..., description="Pressure value")
    unit: str = Field(
        ...,
        description="Pressure unit, e.g., 'bar', 'atm', 'Pa'"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow"
    )


class Volume(BaseModel):
    """
    Volume model for input validation

    Attributes
    ----------
    value : float
        Volume value.
    unit : str
        Volume unit, e.g., 'L', 'm3', 'cm3'.
    """
    value: float = Field(..., description="Volume value")
    unit: str = Field(
        ...,
        description="Volume unit, e.g., 'L', 'm3', 'cm3'"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow"
    )


class CustomProp(BaseModel):
    """
    Custom property model for input validation

    Attributes
    ----------
    value : float | int
        Value of the property, e.g., 'enthalpy', 'entropy'.
    unit : str
        Unit of the property, e.g., 'J/mol.K', 'kJ/mol'.
    """
    value: float | int = Field(
        ...,
        description="Value of the property, e.g., 'enthalpy', 'entropy'"
    )
    unit: str = Field(
        ...,
        description="Unit of the property, e.g., 'J/mol.K', 'kJ/mol'"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow"
    )
