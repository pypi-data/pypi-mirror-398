"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""

from __future__ import annotations
from batem.core.solar import SolarModel, SolarSystem
from batem.core.weather import get_site_weather_data
from batem.core.utils import TimeSeriesPlotter


if __name__ == '__main__':
    swd = get_site_weather_data('Lille', load_from_year=1980, period_of_interest=('01/03/2024', '31/12/2024'))
    data = {variable: swd.series(variable) for variable in swd.variable_names}
    solar_model = SolarModel(swd)
    solar_system = SolarSystem(solar_model)
    # Add solar irradiance data to the plot
    data['dni'] = solar_model.dni.tolist()  # Direct Normal Irradiance (W/m²)
    data['dhi'] = solar_model.dhi.tolist()  # Diffuse Horizontal Irradiance (W/m²)
    data['ghi'] = solar_model.ghi.tolist()  # Global Horizontal Irradiance (W/m²)
    data['rhi'] = solar_model.rhi.tolist()  # Reflected Horizontal Irradiance (W/m²)
    # Add cardinal direction irradiances
    cardinal_irradiances = solar_model.cardinal_irradiances_W()
    for direction, irradiance_values in cardinal_irradiances.items():
        # Convert to list if needed (handles pandas Series, numpy arrays, or lists)
        if hasattr(irradiance_values, 'tolist'):
            irradiance_list = irradiance_values.tolist()
        elif hasattr(irradiance_values, 'to_list'):
            irradiance_list = irradiance_values.to_list()
        else:
            irradiance_list = list(irradiance_values)
        # Use readable names for the directions (e.g., 'south', 'west', 'east', 'north', 'horizontal_up', 'horizontal_down')
        if hasattr(direction, 'name'):
            direction_name = direction.name.lower()
        else:
            direction_name = str(direction).lower()
        data[f'irradiance_{direction_name}'] = irradiance_list
    print(swd)
    time_series_plotter = TimeSeriesPlotter(data, swd.datetimes)
    time_series_plotter.plot()
