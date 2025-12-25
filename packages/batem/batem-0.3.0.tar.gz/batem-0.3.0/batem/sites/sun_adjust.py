# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from scipy.optimize._optimize import OptimizeResult
from core.solar import SolarModel, Parameters, HorizonMask, SkylineRetriever, matching_error
from core.weather import SiteWeatherData, SWDbuilder
from scipy.optimize import differential_evolution
from time import time


if __name__ == '__main__':
    grenoble_weather_data: SiteWeatherData = SWDbuilder(location='Grenoble', from_requested_stringdate='1/01/2023', to_requested_stringdate='31/12/2023',
                                                                    albedo=0.1, pollution=0.1, self.site_latitude_north_deg=45.190823325765166, longitude_east_deg=5.727264569512632).site_weather_data
    solar_mask = HorizonMask(*SkylineRetriever().get(
        grenoble_weather_data.site_latitude_north_deg, grenoble_weather_data.site_longitude_east_deg))

    grenoble_solar_model = SolarModel(
        site_weather_data=grenoble_weather_data, horizon_mask=solar_mask)
    solar_parameters: Parameters = grenoble_solar_model.parameters
    print(solar_parameters)

    tic = time()
    result: OptimizeResult = differential_evolution(matching_error, bounds=solar_parameters.bounds(), args=(
        grenoble_weather_data, solar_mask), x0=solar_parameters(), workers=-1, maxiter=1000, updating='deferred', polish=True, disp=True)
    print(time()-tic, 'seconds')
    print(result)

    parameters = Parameters(result.x)
    grenoble_solar_model = SolarModel(
        grenoble_weather_data, parameters=parameters, horizon_mask=solar_mask)
    print(parameters)

    # grenoble_weather_data.add_variable('calculated tsi', 'W/m2', grenoble_solar_model.tsi)
    # grenoble_weather_data.add_variable('calculated dni', 'W/m2', grenoble_solar_model.dni)
    # grenoble_weather_data.add_variable('calculated dhi', 'W/m2', grenoble_solar_model.dhi)
    # grenoble_weather_data.add_variable('calculated ghi', 'W/m2', grenoble_solar_model.ghi)
    # grenoble_weather_data.add_variable('calculated gni', 'W/m2', grenoble_solar_model.gni)

    # TimeSeriesPlotter(variable_values={'gni': grenoble_solar_model.gni, 'ghi': grenoble_solar_model.ghi, 'direct_radiation_instant': grenoble_weather_data.series('direct_radiation_instant')}, datetimes=grenoble_weather_data.datetimes, units={'gni': 'W/m2', 'direct_radiation_instant': 'W/m2'})
