# import libs
from typing import Any, Dict, Callable
from pydantic import BaseModel, Field, ConfigDict
from pyThermoDB.core import TableEquation
from pythermodb_settings.models import Temperature


# NOTE: enthalpy of formation result model
class ComponentEnthalpyOfFormation(BaseModel):
    '''
    Component Enthalpy of Formation Result Model

    Attributes
    ----------
    temperature : Temperature
        The temperature at which the enthalpy of formation is calculated.
    value : float
        The enthalpy of formation value.
    unit : str
        The enthalpy of formation unit.
    symbol : str
        The enthalpy of formation symbol.
    '''
    model_config = ConfigDict(arbitrary_types_allowed=True)

    temperature: Temperature = Field(
        ...,
        description="The temperature at which the enthalpy of formation is calculated."
    )

    value: float = Field(
        ...,
        description="The enthalpy of formation value."
    )
    unit: str = Field(
        ...,
        description="The enthalpy of formation unit."
    )
    symbol: str = Field(
        ...,
        description="The enthalpy of formation symbol."
    )


# NOTE: gibbs energy of formation result model


class ComponentGibbsEnergyOfFormation(BaseModel):
    '''
    Component Gibbs Energy of Formation Result Model

    Attributes
    ----------
    temperature : Temperature
        The temperature at which the Gibbs energy of formation is calculated.
    value : float
        The Gibbs energy of formation value.
    unit : str
        The Gibbs energy of formation unit.
    symbol : str
        The Gibbs energy of formation symbol.
    '''
    model_config = ConfigDict(arbitrary_types_allowed=True)

    temperature: Temperature = Field(
        ...,
        description="The temperature at which the Gibbs energy of formation is calculated."
    )

    value: float = Field(
        ...,
        description="The Gibbs energy of formation value."
    )
    unit: str = Field(
        ...,
        description="The Gibbs energy of formation unit."
    )
    symbol: str = Field(
        ...,
        description="The Gibbs energy of formation symbol."
    )
