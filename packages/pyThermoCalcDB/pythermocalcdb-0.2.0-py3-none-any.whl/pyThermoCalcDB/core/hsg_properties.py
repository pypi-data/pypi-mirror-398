# import libs
import logging
from typing import Dict, Any, Literal, Optional, List
from pythermodb_settings.models import Component, Temperature
from pythermodb_settings.utils import set_component_id
import pycuc
from pyThermoLinkDB.thermo import Source
from pyThermoLinkDB.models.component_models import ComponentEquationSource
# local
from ..configs.thermo_props import (
    EnFo_IG_UNIT,
    Ent_STD_UNIT,
    GiEnFo_IG_UNIT,
    EnFo_IG_SYMBOL,
    Ent_STD_SYMBOL,
    GiEnFo_IG_SYMBOL,
    Cp_IG_SYMBOL,
    Cp_IG_UNIT
)
from ..utils.math_tools import integrate_function
from .calc import Cp_integral, Cp__RT_integral
from ..models import (
    ComponentEnthalpyOfFormation,
    ComponentGibbsEnergyOfFormation
)

# NOTE: Logger
logger = logging.getLogger(__name__)


class HSGProperties:
    """
    HSG Properties class to calculate enthalpy and entropy of formation, and Gibbs free energy of formation for a given compound.

    Attributes
    ----------
    component : Component
        The chemical component for which HSG properties are to be calculated.
    source : Source
        The source containing data for calculations.
    """
    # NOTE: attributes
    T_ref = 298.15  # reference temperature in K
    R = 8.3145  # universal gas constant in J/mol·K

    def __init__(
        self,
        component: Component,
        source: Source,
        component_key: Literal[
            'Name-State',
            'Formula-State',
            'Name',
            'Formula',
            'Name-Formula-State',
            'Formula-Name-State'
        ] = 'Name-State',
    ) -> None:
        """
        Initialize HSGProperties with a component and source.

        Parameters
        ----------
        component : Component
            The chemical component for which HSG properties are to be calculated, it consists of the following attributes:
                - name: str
                - formula: str
                - state: str
                - mole_fraction: float, optional
        source : Source
            The source containing data for calculations.
        component_key : Literal
            The key to identify the component in the source data. Defaults to 'Name-State'.
        """
        # NOTE: component
        self.component = component
        # NOTE: source
        self.source = source
        # NOTE: component key
        self.component_key = component_key

        # >> set component id
        self.component_id = set_component_id(
            component=self.component,
            component_key=self.component_key
        )

        # SECTION: extract component source
        self.component_source = self.source.get_component_data(
            component_id=self.component_id,
            components=[self.component],
            component_key=self.component_key
        )

        # SECTION: retrieve heat capacity equation source
        self.Cp_eq_src = self._get_Cp_equation_source()

    def _get_formation_data(self, prop_name: str) -> Optional[Dict[str, Any]]:
        '''
        Retrieve formation data for the specified property.

        Parameters
        ----------
        prop_name : str
            The name of the property for which formation data is to be retrieved.

        Returns
        -------
        Optional[Dict[str, Any]]
            A dictionary containing the formation data if available, otherwise None.
        '''
        try:
            res = self.source.data_extractor(
                component_id=self.component_id,
                prop_name=prop_name,
            )

            return res
        except Exception as e:
            logger.exception(
                f"Error retrieving formation data for {prop_name}: {e}")
            return None

    def _get_Cp_equation_source(self) -> ComponentEquationSource:
        '''
        Retrieve the heat capacity equation source for the component.

        Returns
        -------
        ComponentEquationSource
            The heat capacity equation source if available, otherwise None.
        '''
        try:
            # NOTE: build equation
            Cp_eq_src = self.source.eq_builder(
                components=[self.component],
                prop_name=Cp_IG_SYMBOL,
                component_key=self.component_key  # type: ignore
            )

            # >> check Cp equation
            if Cp_eq_src is None:
                logger.warning(
                    f"No heat capacity equation available for component {self.component_id}.")
                raise ValueError("No heat capacity equation source found.")

            # >> for component
            component_Cp_eq_src: ComponentEquationSource | None = Cp_eq_src.get(
                self.component_id
            )

            if component_Cp_eq_src is None:
                logger.warning(
                    f"No heat capacity equation available for component {self.component_id}.")
                raise ValueError("No heat capacity equation source found.")

            return component_Cp_eq_src
        except Exception as e:
            logger.exception(
                f"Error retrieving heat capacity equation source: {e}")
            raise

    def _calc_enthalpy_change(
            self,
            Cp_eq_src: ComponentEquationSource,
            T1: float,
            T2: float
    ) -> Optional[float]:
        '''
        Calculate the enthalpy change between two temperatures using the provided equation source.

        Parameters
        ----------
        Cp_eq_src : ComponentEquationSource
            The equation source for heat capacity.
        T1 : float
            The initial temperature in K.
        T2 : float
            The final temperature in K.

        Returns
        -------
        Optional[float]
            The calculated enthalpy change in J/mol if successful, otherwise None.
        '''
        try:
            delta_H = Cp_integral(
                eq_src=Cp_eq_src,
                T_ref=T1,
                T=T2,
            )

            # >> check
            if delta_H is None:
                logger.error(
                    f"Failed to calculate enthalpy change from {T1} K to {T2} K.")
                return None

            return float(delta_H)
        except Exception as e:
            logger.exception(
                f"Error calculating enthalpy change from {T1} K to {T2} K: {e}")
            return None

    def calc_enthalpy_of_formation(
            self,
            temperature: Temperature
    ) -> Optional[ComponentEnthalpyOfFormation]:
        '''
        Calculate the enthalpy of formation at a given temperature.

        Parameters
        ----------
        temperature : Temperature
            The temperature at which to calculate the enthalpy of formation.

        Returns
        -------
        Optional[ComponentEnthalpyOfFormation]
            A ComponentEnthalpyOfFormation object containing the calculated enthalpy of formation if successful, otherwise None.
        '''
        try:
            # SECTION: temperature value
            T_val = temperature.value
            T_unit = temperature.unit

            # >> convert temperature to K if necessary
            # ! K
            if T_unit != 'K':
                T_val = pycuc.to(
                    T_val,
                    f"{T_unit} => K"
                )

            # SECTION: get formation data
            # >> enthalpy of formation (EnFo_IG) unit ?
            formation_data = self._get_formation_data(EnFo_IG_SYMBOL)

            # >> check formation data
            if formation_data is None:
                logger.warning(
                    f"No formation data available for enthalpy of formation.")
                return None

            # NOTE: unit conversion if necessary
            # TODO: convert to [J/mol]
            EnFo_val = formation_data['value']
            EnFo_unit = formation_data['unit']
            # ! to [J/mol]
            unit_ = f"{EnFo_unit} => {EnFo_IG_UNIT}"
            EnFo_IG_val = pycuc.to(
                EnFo_val,
                unit_
            )

            # SECTION: heat capacity calculation
            # NOTE: integrate Cp from T_ref to T
            # ! [J/mol]
            delta_Cp_val = self._calc_enthalpy_change(
                Cp_eq_src=self.Cp_eq_src,
                T1=self.T_ref,
                T2=T_val,
            )

            # >> check
            if delta_Cp_val is None:
                logger.error(
                    f"Failed to integrate Cp equation from T={self.T_ref} K to T={T_val} K.")
                return None

            # SECTION: calculate enthalpy of formation at temperature
            # ! J/mol
            EnFo_IG_T_val = EnFo_IG_val + delta_Cp_val

            # SECTION: prepare result
            result_ = {
                'temperature': temperature,
                'value': EnFo_IG_T_val,
                'unit': EnFo_IG_UNIT,
                'symbol': EnFo_IG_SYMBOL
            }

            # >> set
            result = ComponentEnthalpyOfFormation(**result_)
            return result
        except Exception as e:
            logger.exception(
                f"Error calculating enthalpy of formation: {e}")
            return None

    def calc_enthalpy_of_formation_range(
            self,
            temperatures: list[Temperature]
    ) -> List[ComponentEnthalpyOfFormation]:
        '''
        Calculate the enthalpy of formation over a range of temperatures.

        Parameters
        ----------
        temperatures : list[Temperature]
            A list of temperatures at which to calculate the enthalpy of formation.

        Returns
        -------
        list[ComponentEnthalpyOfFormation]
            A list of ComponentEnthalpyOfFormation objects containing the calculated enthalpy of formation at each temperature.
        '''
        results = []
        try:
            for temp in temperatures:
                result = self.calc_enthalpy_of_formation(temperature=temp)
                if result is not None:
                    results.append(result)
            return results
        except Exception as e:
            logger.exception(
                f"Error calculating enthalpy of formation over range: {e}")
            return results

    def calc_gibbs_free_energy_of_formation(
            self,
            temperature: Temperature
    ) -> Optional[ComponentGibbsEnergyOfFormation]:
        '''
        Calculate the Gibbs free energy of formation at a given temperature.

        Parameters
        ----------
        temperature : Temperature
            The temperature at which to calculate the Gibbs free energy of formation.

        Returns
        -------
        Optional[ComponentGibbsEnergyOfFormation]
            A ComponentGibbsEnergyOfFormation object containing the calculated Gibbs free energy of formation if successful, otherwise None.
        '''
        try:
            # SECTION: temperature value
            T_val = temperature.value
            T_unit = temperature.unit

            # >> convert temperature to K if necessary
            if T_unit != 'K':
                T_val = pycuc.to(
                    T_val,
                    f"{T_unit} => K"
                )

            # SECTION: get formation data
            # >> enthalpy of formation (EnFo_IG) unit ?
            formation_data = self._get_formation_data(EnFo_IG_SYMBOL)
            # >> gibbs energy of formation (GiEnFo_IG) unit ?
            gibbs_formation_data = self._get_formation_data(GiEnFo_IG_SYMBOL)

            # >> check formation data
            if formation_data is None:
                logger.warning(
                    f"No formation data available for enthalpy of formation.")
                return None

            if gibbs_formation_data is None:
                logger.warning(
                    f"No formation data available for Gibbs free energy of formation.")
                return None

            # NOTE: unit conversion if necessary
            # TODO: convert to [J/mol]
            EnFo_IG_val = formation_data['value']
            EnFo_IG_unit = formation_data['unit']
            # ! to [J/mol]
            unit_ = f"{EnFo_IG_unit} => {EnFo_IG_UNIT}"
            EnFo_IG_val = pycuc.to(
                EnFo_IG_val,
                unit_
            )

            GiEnFo_IG_val = gibbs_formation_data['value']
            GiEnFo_IG_unit = gibbs_formation_data['unit']
            # ! to [J/mol]
            unit_ = f"{GiEnFo_IG_unit} => {GiEnFo_IG_UNIT}"
            GiEnFo_IG_val = pycuc.to(
                GiEnFo_IG_val,
                unit_
            )

            # SECTION: heat capacity calculation
            # NOTE: integrate Cp from T_ref to T
            # ! [J/mol]
            _eq_Cp_integral = self._calc_enthalpy_change(
                Cp_eq_src=self.Cp_eq_src,
                T1=self.T_ref,
                T2=T_val,
            )

            # >> check
            if _eq_Cp_integral is None:
                logger.error(
                    f"Failed to integrate Cp equation from T={self.T_ref} K to T={T_val} K.")
                return None

            # NOTE: integrate Cp/RT from T_ref to T
            # ! dimensionless
            _eq_Cp_integral_Cp__RT = Cp__RT_integral(
                eq_src=self.Cp_eq_src,
                T_ref=self.T_ref,
                T=T_val,
                R=self.R
            )

            # >> check
            if _eq_Cp_integral_Cp__RT is None:
                logger.error(
                    f"Failed to integrate Cp/RT equation from T={self.T_ref} K to T={T_val} K.")
                return None

            # SECTION: calculate Gibbs free energy of formation at temperature
            # ! Gibbs free energy of formation at T [J/mol]
            # A [J/mol]
            A = (GiEnFo_IG_val - EnFo_IG_val)/(self.R*self.T_ref)
            # B
            B = EnFo_IG_val/(self.R*T_val)
            # C
            C = (1/T_val)*_eq_Cp_integral/self.R
            # D
            D = _eq_Cp_integral_Cp__RT
            # E
            E = A + B + C - D
            # at T [J/mol]
            GiEn_IG_T = float(E*self.R*T_val)

            # SECTION: prepare result
            result = {
                'temperature': temperature,
                'value': GiEn_IG_T,
                'unit': GiEnFo_IG_UNIT,
                'symbol': GiEnFo_IG_SYMBOL
            }

            # >> set
            result = ComponentGibbsEnergyOfFormation(**result)

            return result
        except Exception as e:
            logger.exception(
                f"Error calculating Gibbs free energy of formation: {e}")
            return None

    def calc_gibbs_free_energy_of_formation_range(
            self,
            temperatures: list[Temperature]
    ) -> List[ComponentGibbsEnergyOfFormation]:
        '''
        Calculate the Gibbs free energy of formation over a range of temperatures.

        Parameters
        ----------
        temperatures : list[Temperature]
            A list of temperatures at which to calculate the Gibbs free energy of formation.

        Returns
        -------
        list[ComponentGibbsEnergyOfFormation]
            A list of ComponentGibbsEnergyOfFormation objects containing the calculated Gibbs free energy of formation at each temperature.
        '''
        results = []
        try:
            for temp in temperatures:
                result = self.calc_gibbs_free_energy_of_formation(
                    temperature=temp)
                if result is not None:
                    results.append(result)
            return results
        except Exception as e:
            logger.exception(
                f"Error calculating Gibbs free energy of formation over range: {e}")
            return results
