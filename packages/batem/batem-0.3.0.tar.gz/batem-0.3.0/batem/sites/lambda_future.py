# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from __future__ import annotations
import core.lambdahouse
import core.weather
import core.library
import core.solar
import time
import sys
import matplotlib.pyplot as plt

weather_file: str = 'Grenoble.json'
location: str = 'Grenoble'
weather_year = 2050
latitude_north_deg, longitude_east_deg = 45.19154994547585, 5.722065312331381


class MyConfiguration(core.lambdahouse.LambdaParametricData):

    def __init__(self, location: str, latitude: float, longitude: float, weather_year: int, albedo: float = 0.1, pollution: float = 0.1) -> None:
        super().__init__(location, latitude, longitude, weather_year, albedo, pollution)

        self.section('house')
        self(total_living_surface=100)
        self(height_per_floor=2.5)
        self(shape_factor=1, parametric=[.25, .5, .75, 1, 1.25, 1.5, 1.75, 2, 3])
        self(number_of_floors=1, parametric=[1, 2, 3])
        self(wall_composition_in_out=[('concrete', 14e-2), ('plaster', 15e-3), ('polystyrene', 20e-2)])
        self(roof_composition_in_out=[('plaster', 30e-3), ('polystyrene', 9e-2), ('concrete', 13e-2)])
        self(glass_composition_in_out=[('glass', 4e-3), ('air', 6e-3), ('glass', 4e-3)])
        self(ground_composition_in_out=[('concrete', 13e-2), ('polystyrene', 30e-2), ('gravels', 20e-2)])
        self.insulation: str = 'polystyrene'  # be careful: no space in the material used for insulation
        self(polystyrene=20e-2, parametric=[0, 5e-2, 10e-2, 15e-2, 20e-2, 25e-2, 30e-2, 35e-2, 40e-2])
        self.section('windows')
        self(offset_exposure=0, parametric=[offset_exposure for offset_exposure in range(-45, 45, 5)])
        self(glazing={'north': 0.1, 'west': 0.1, 'east': 0.1, 'south': 0.1}, parametric=[0.05, .2, .4, .6, .8])
        self(solar_factor=0.8)
        self(south_solar_protection_angle=0, parametric=[0, 15, 30, 35, 40, 45, 50, 55, 60, 65, 70])

        self.section('HVAC and photovoltaic (PV) systems')
        self(heating_setpoint=21, parametric=[18, 19, 20, 22, 23])
        self(delta_temperature_absence_mode=3, parametric=[0, 1, 2, 3, 4])
        self(cooling_setpoint=26, parametric=[23, 24, 25, 27, 28, 29])
        self(winter_hvac_trigger_temperature=20)
        self(summer_hvac_trigger_temperature=26)
        self(hvac_hour_delay_for_trigger=24)
        self(hvac_COP=3)
        self(PV_surface=20, parametric=[2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22])
        self(final_to_primary_energy_coefficient=2.54)
        self(air_renewal_presence=1, parametric=[.5, 1, 2, 3])  # in vol/h
        self(air_renewal_absence=.1)
        self(ventilation_heat_recovery_efficiency=0.8, parametric=[0, .25, .5, .7, .9])
        self(PV_efficiency=0.20)

        self.section('inhabitants')
        self(occupancy_schema={(1, 2, 3, 4, 5): {(18, 7): 4, (7, 18): 0}, (6, 7): {(0, 24): 4}})  # days of weeks (1=Monday,...), period (start. hour, end. hour) : avg occupancy
        self(average_occupancy_electric_gain=50)
        self(average_occupancy_metabolic_gain=100)
        self(average_permanent_electric_gain=200)
        self(air_renewal_overheat_threshold=26)
        self(air_renewal_overheat=5)


configuration: MyConfiguration = MyConfiguration(location=location, weather_year=weather_year, latitude=latitude_north_deg, longitude=longitude_east_deg)

on_screen = False
experiment: core.lambdahouse.ReportGenerator = core.lambdahouse.ReportGenerator(configuration, on_screen=on_screen)
analysis: core.lambdahouse.Analyzes = core.lambdahouse.Analyzes(experiment)

print(configuration)
tstart = time.time()
analysis.climate(experiment)
analysis.evolution(experiment)
analysis.solar(experiment)
analysis.house(experiment)
analysis.neutrality(experiment)
print(f'duration {round((time.time() - tstart)/60, 1)} min', file=sys.stderr)
