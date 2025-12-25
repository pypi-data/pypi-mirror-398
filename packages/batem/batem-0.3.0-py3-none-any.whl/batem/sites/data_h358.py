"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0


Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
from batem.core.solar import SolarModel, SolarSystem, RectangularMask, Collector
from batem.core.data import DataProvider, Bindings


def generate_h358_data_provider(starting_stringdate: str = '15/02/2015', ending_stringdate: str = '15/02/2016') -> DataProvider:

    deleted_variables: tuple[str] = ('Tyanis', 'zetaW7', 'zetaW9', 'wind_direction_in_deg', 'feels_like', 'occupancy', 'temp_min', 'temp_max', 'description', 'power_heater', 'et0_fao_evapotranspiration', 'vapor_pressure_deficit',  'is_day', 'shortwave_radiation', 'direct_radiation', 'diffuse_radiation', 'direct_normal_irradiance')  # 'pressure_msl', 'surface_pressure'

    latitude_north_deg, longitude_east_deg = 45.19154994547585, 5.722065312331381
    bindings = Bindings()

    dp = DataProvider(location='Grenoble', latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg, csv_measurement_filename='h358data_2015-2016.csv', starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate, bindings=bindings, albedo=0.1, pollution=0.1, number_of_levels=4, deleted_variables=deleted_variables)

    dp.add_param('body_metabolism', 100, (30, 120, 10))
    dp.add_param('body_PCO2', 7, (2, 10, 1))
    dp.add_param('volume:office', 56)
    dp.add_param('permanent_power:office', 100, (0, 500, 25))
    dp.add_param('Q_0:office-outdoor', 10/3600, (1/3600, 15/3600, 1/3600))
    dp.add_param('Q_window:office-outdoor', 5500/3600, (1000/3600, 10000/3600, 10/3600))
    dp.add_param('Q_door:office-outdoor', 1000/3600, (500/3600, 2000/3600, 10/3600))
    dp.add_param('Q_0:office-corridor', 30/3600, (1/3600, 50/3600, 1/3600))
    dp.add_param('Q_window:corridor-office', 5500/3600, (10/3600, 10000/3600, 10/3600))
    dp.add_param('Q_door:corridor-office', 1000/3600, (500/3600, 2000/3600, 10/3600))
    dp.add_param('slab_surface_correction:downstairs-office', 1)  # , (1, 3, .1)
    dp.add_param('heater_power_per_delta_surface_temperature:office', 50, (30, 200, 10))
    dp.add_param('psi_bridge:office-outdoor', 0.5 * 0.99)  # , (0.0 * 0.99, 0.5 * 5, 0.1)
    dp.add_param('foam_thickness:office-outdoor', 34e-3)  # , (10e-3, 50e-3, 10e-3)
    dp.add_param('solar_factor:office-outdoor', 0.8, (0, 1, .1))
    dp.add_param('TZ:downstairs', 20, (16, 25, 1))
    dp.add_param('CCO2:outdoor', 400, (250, 650, 50))
    dp.add_param('Rfactor:office-outdoor', 1, (.5, 2, .1))
    dp.add_param('Rfactor:corridor-office', 1, (.5, 2, .1))
    dp.add_param('Rfactor:downstairs-office', 1, (.5, 2, .1))
    dp.add_param('Cfactor:office-outdoor', 1, (.1, 10, .1))
    dp.add_param('Cfactor:corridor-office', 1, (.1, 10, .1))
    dp.add_param('Cfactor:downstairs-office', 1, (.1, 10, .1))
    # Temperature offset parameter for sensor calibration (can be tuned during parameter estimation)
    dp.add_param('temperature_offset:office', 0.0, (-3.0, 3.0, 0.1))  # (min, max, resolution) in °C

    window_mask = RectangularMask((-86, 60), (20, 68), inverted=True)
    solar_model = SolarModel(dp.weather_data)
    solar_system = SolarSystem(solar_model)

    Collector(solar_system, 'main', surface_m2=2, exposure_deg=-13, slope_deg=90, solar_factor=1, close_mask=window_mask)
    solar_gains_with_mask = solar_system.powers_W(gather_collectors=True)

    # Align solar gains time series with measurement timestamps.
    # The raw solar gains are computed on the weather time base, which may differ
    # from the measurement time base (e.g. daylight saving adjustments).
    # Use the same alignment helper as other weather-derived variables to ensure
    # we have exactly one value per measurement time step.
    try:
        aligned_solar_gains = dp._align_weather_data(solar_gains_with_mask, 'Psun_hitting_window:office')
        if aligned_solar_gains is not None and len(aligned_solar_gains) == len(dp):
            dp.add_var('Psun_hitting_window:office', aligned_solar_gains)
        else:
            # Fallback: trim or pad the series to match the DataProvider length
            if len(solar_gains_with_mask) >= len(dp):
                dp.add_var('Psun_hitting_window:office', solar_gains_with_mask[:len(dp)])
            else:
                padded = list(solar_gains_with_mask) + [solar_gains_with_mask[-1]] * (len(dp) - len(solar_gains_with_mask))
                dp.add_var('Psun_hitting_window:office', padded)
    except Exception:
        # As a last resort, trim the series to the DataProvider length
        if len(solar_gains_with_mask) >= len(dp):
            dp.add_var('Psun_hitting_window:office', solar_gains_with_mask[:len(dp)])
        else:
            padded = list(solar_gains_with_mask) + [solar_gains_with_mask[-1]] * (len(dp) - len(solar_gains_with_mask))
            dp.add_var('Psun_hitting_window:office', padded)

    # build invariant variables
    detected_motions: list[int] = [int(d > 1) for d in dp.series('detected_motions')]
    power_stephane: list[float] = dp.series('power_stephane')
    power_khadija: list[float] = dp.series('power_khadija')
    power_audrey: list[float] = dp.series('power_audrey')
    power_stagiaire: list[float] = dp.series('power_stagiaire')

    occupancy: list[int] = [max(detected_motions[k], int(power_stephane[k] > 17) + int(power_khadija[k] > 17) + int(power_stagiaire[k] > 17) + int(power_audrey[k] > 17)) for k in range(len(dp))]
    presence: list[int] = [int(occupancy[k] > 0) for k in range(len(dp))]
    dp.add_var('occupancy:office', occupancy)
    dp.add_var('presence:office', presence)

    dp.add_parameterized('Pmetabolism:office', lambda k: dp('body_metabolism') * dp('occupancy:office', k), default=0, resolution=10)

    dp.add_parameterized('Pwindow:office', lambda k: dp('solar_factor:office-outdoor') * dp('Psun_hitting_window:office', k), default=0, resolution=10)

    dp.add_parameterized('GAIN:office', lambda k:  dp('total_electric_power', k) + dp('occupancy:office', k) * dp('body_metabolism') + dp('solar_factor:office-outdoor') * dp('Psun_hitting_window:office', k) + dp('permanent_power:office'), default=0, resolution=10)
    dp.add_parameterized('PHVAC:office', lambda k: dp('heater_power_per_delta_surface_temperature:office') * dp('dT_heat', k), default=0, resolution=10)

    # PZ:office is the total power = GAIN:office + PHVAC:office (if PHVAC exists, otherwise just GAIN)
    def compute_PZ_office(k):
        gain = dp('GAIN:office', k)
        try:
            phvac = dp('PHVAC:office', k)
            return gain + phvac
        except (KeyError, ValueError):
            return gain

    dp.add_parameterized('PZ:office', compute_PZ_office, default=0, resolution=10)

    dp.add_parameterized('PCO2:office', lambda k: dp('body_PCO2') * dp('occupancy:office', k), default=0, resolution=100)
    dp.add_parameterized('Q:office-outdoor', lambda k: dp('Q_0:office-outdoor') + dp('Q_window:office-outdoor') * dp('window_opening', k) + dp('Q_door:office-corridor') * dp('door_opening', k), default=0, resolution=15/3600)
    dp.add_parameterized('Q:office-corridor', lambda k: dp('Q_0:office-corridor') + dp('Q_window:office-corridor') * dp('window_opening', k) + dp('Q_door:office-corridor') * dp('door_opening', k), default=0, resolution=15/3600)

    # Create parameterized variable that applies the temperature offset to measured temperature
    dp.add_parameterized('Toffice_reference_offset',
                         lambda k: dp('Toffice_reference', k) + dp('temperature_offset:office'),
                         default=0.0, resolution=0.1)

    # Use offset-adjusted measured temperature for model comparison
    bindings.link_model_data('TZ:office', 'Toffice_reference_offset')
    bindings.link_model_data('TZ:corridor', 'Tcorridor')
    bindings.link_model_data('TZ:outdoor', 'weather_temperature')
    bindings.link_model_data('CCO2:corridor', 'corridor_CO2_concentration')
    bindings.link_model_data('CCO2:office', 'office_CO2_concentration')
    bindings.link_model_data('z_window:office-outdoor', 'window_opening')
    bindings.link_model_data('z_door:office-corridor', 'door_opening')

    # Process bindings to create aliases for internal variables
    dp.bindings.create_internal_aliases(dp)

    return dp


if __name__ == '__main__':
    # print(h358_data_provider('datetime', all=True))
    dp_full: DataProvider = generate_h358_data_provider()
    print('full:', dp_full)
    # dp: DataProvider = dp_full.excerpt(starting_stringdate='1/03/2015', ending_stringdate='20/03/2015')
    # print(dp('office-corridor:Q_door', 3))
    # dp('office-corridor:Q_door', value=18, k=3)
    # print(dp('office-corridor:Q_door', k=3))
    # print(dp('TZcorridor', 3))
    # print(dp('Tcorridor'))
    # # print(dp('corridor:Temperature', k=None))
    # print(dp('office:Pmetabolism', 3))
    # print(dp('office:Pmetabolism'))
    # print(dp('office-corridor:Q', 30))
    # print(dp('corridor-office:Q', 30))
    # print()

    # for k in range(len(dp)):
    #     print(dp.fingerprint(k), dp('door_opening', k), dp('window_opening', k))

    # print('excerpt:', dp.fingerprint(None))
    dp_full.plot()
