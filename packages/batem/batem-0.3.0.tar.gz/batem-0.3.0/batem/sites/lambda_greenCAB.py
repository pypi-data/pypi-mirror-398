"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""

from __future__ import annotations
import time
import core.lambdahouse

# Use the library to load a physical property related to a sheet name from the from the 'propertiesDB.xlsx' file, and a row number.
# parameter1: short name used to refer to a material or a component
# parameter2: sheet name in the xlsx file where the property is
# parameter3: row in the sheet of the file containing the property loaded for local usage
# For instance, to load the thermal properties of the material 'Expanded Polystyrene – IN31', sheet 'thermal', row 170


class MyConfiguration(core.lambdahouse.LambdaParametricData):

    def __init__(self, location: str, latitude: float, longitude: float, weather_year: int, albedo: float = 0.1, pollution: float = 0.1) -> None:
        super().__init__(location, latitude, longitude, weather_year, albedo, pollution)

        self.section('house')
        self(total_living_surface=18)
        self(height_per_floor=2.38)
        self(shape_factor=.2)
        self(number_of_floors=1)
        self(wall_composition_in_out=[('wood', 3e-3), ('polystyrene', 15e-2), ('steel', 5e-3), ('wood', 6e-3)])
        self(roof_composition_in_out=[('wood', 3e-3), ('polystyrene', 15e-2), ('steel', 5e-3)])
        self(glass_composition_in_out=[('glass', 4e-3), ('air', 12e-3), ('glass', 4e-3)])
        self(ground_composition_in_out=[('wood', 10e-3), ('polystyrene', 15e-2), ('steel', 5e-3)])
        self.insulation: str = 'polystyrene'  # be careful: no space in the material used for insulation
        self(polystyrene=0e-2, parametric=[0, 5e-2, 10e-2, 15e-2, 20e-2, 25e-2, 30e-2])
        self.section('windows')
        self(offset_exposure=-5, parametric=[offset_exposure for offset_exposure in range(-45, 45, 5)])
        self(glazing={'north': 0, 'west': 0, 'east': 0.3, 'south': 0}, parametric=[0, .2, .3, .4, .6, .8])
        self(solar_factor=0.4, parametric=[.1, .2, .3, .4, .5, .6, .7, .8, .9])
        self(south_solar_protection_angle=0)

        self.section('HVAC and photovoltaic (PV) systems')
        self(heating_setpoint=21, parametric=[18, 19, 20, 22, 23])
        self(delta_temperature_absence_mode=3, parametric=[0, 1, 2, 3, 4])
        self(cooling_setpoint=26, parametric=[23, 24, 25, 27, 28, 29])
        self(winter_hvac_trigger_temperature=16)
        self(summer_hvac_trigger_temperature=24)
        self(hvac_hour_delay_for_trigger=24)
        self(inertia_level=6, parametric=[3, 6, 9, 12, 15, 18, 21, 24])
        self(hvac_COP=2.5)
        self(PV_surface=12, parametric=[1, 2, 4, 6, 9, 14, 18])
        self(final_to_primary_energy_coefficient=2.54)
        self(air_renewal_presence=.1, parametric=[.5, 1, 2, 3])  # in vol/h
        self(air_renewal_absence=.1)
        self(ventilation_heat_recovery_efficiency=0, parametric=[0, .25, .5, .7, .9])
        self(PV_efficiency=0.20)

        self.section('inhabitants')
        self(occupancy_schema={(1, 2, 3, 4, 5,): {(9, 19): 3}})  # days of weeks (1=Monday,...), period (start. hour, end. hour) : avg occupancy
        self(average_occupancy_electric_gain=160)
        self(average_occupancy_metabolic_gain=100)
        self(average_permanent_electric_gain=0)
        self(air_renewal_overheat_threshold=26)
        self(air_renewal_overheat=5)


if __name__ == '__main__':
    weather_file = 'greenCAB'
    weather_year = 2022
    location = 'Saint-Julien-en-Saint-Alban'
    latitude, longitude = 44.753678, 4.696513

    configuration = MyConfiguration(location=location, latitude=latitude, longitude=longitude, weather_year=weather_year)
    tini = time.time()
    experiment = core.lambdahouse.ReportGenerator(configuration, on_screen=False)
    analysis = core.lambdahouse.Analyzes(experiment)  # 1
    analysis.climate(experiment)  # 2
    analysis.evolution(experiment)  # 3
    analysis.solar(experiment)  # 4
    analysis.house(experiment)  # 5
    analysis.neutrality(experiment)  # 6
    experiment.close()  # 7
    print('duration: %i minutes' % (int(round((time.time() - tini) / 60))))
