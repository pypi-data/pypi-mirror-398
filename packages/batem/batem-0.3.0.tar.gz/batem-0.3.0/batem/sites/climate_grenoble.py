"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
from batem.core.weather import WeatherJsonReader, SiteWeatherData
from batem.core.climate import ProspectiveClimateDRIAS, HistoricalDatabase, MinMerger, AvgMerger, MaxMerger, SumMerger, Merger, ProspectiveClimateRefiner


if __name__ == '__main__':
    ################################################################
    # drias_filename = 'ALADIN63_rcp2.6.txt'
    location = 'Grenoble'
    drias_filename = 'RACMO22E_rcp2.6.txt'
    latitude, longitude = 45.190823325765166, 5.727264569512632
    # drias_filename = 'RACMO22E-rcp2.6.txt'

    prospective_period = (None, None)
    # prospective_period = ('1/1/2006', '31/12/2023')
    reference_period = ('1/1/2006', '31/12/2023')

    # prospective_period = ('1/1/2050', '31/12/2050')
    # prospective_period = ('1/1/2100', '31/12/2100')
    # reference_period = ('1/1/2023', '31/12/2023')

    feature_merger_weights: dict[Merger, float] = {
        MinMerger('temperature'): 1,
        MaxMerger('temperature'): 1,
        AvgMerger('temperature'): 1,
        SumMerger('precipitation_mass'): 1,
        AvgMerger('absolute_humidity'): 1,
        AvgMerger('direct_normal_irradiance_instant'): 1,
        AvgMerger('wind_speed_m_per_s'): 1,
        SumMerger('snowfall_mass'): 1
    }
    ################################################################
    
    print(WeatherJsonReader(location=location, latitude_north_deg=latitude, longitude_east_deg=longitude).site_weather_data)

    prospective_climate = ProspectiveClimateDRIAS(
        filename=drias_filename, starting_stringdate=prospective_period[0], ending_stringdate=prospective_period[1])

    print('Climate prospective:', prospective_climate)

    historical_database = HistoricalDatabase(WeatherJsonReader(location=location, latitude_north_deg=latitude, longitude_east_deg=longitude).site_weather_data, feature_merger_weights)
    print(historical_database)

    historical_database.plot_prospective_comparison(prospective_climate)

    pcr = ProspectiveClimateRefiner(prospective_climate=prospective_climate, historical_database=historical_database)
    prospective_site_weather_data: SiteWeatherData = pcr.make_prospective_site_weather_data('Grenoble')

    # print('plotting results')
    # pcr.actual_prospective_plot()

    # Experiment.plot_givoni(pcr.historical_database.site_weather_data('temperature'), pcr.historical_database.site_weather_data('absolute_humidity'), 'reference')
    # Experiment.plot_givoni(prospective_site_weather_data('temperature'), prospective_site_weather_data('absolute_humidity'), 'prospective')

    # site_weather_data: SiteWeatherData = pcr.historical_database.site_weather_data.excerpt(from_stringdate='1/1/2023', to_stringdate='31/12/2023')

    # Experiment.plot_rain('reference precipitation', site_weather_data.datetimes, site_weather_data('precipitation'))
    # Experiment.plot_rain('prospective precipitation', pcr.datetimes, prospective_site_weather_data('precipitation'))

    # Experiment.plot_month_week_averages('reference precipitation', site_weather_data.datetimes, site_weather_data('precipitation'))
    # Experiment.plot_month_week_averages('prospective precipitation', pcr.datetimes, prospective_site_weather_data('precipitation'))

    # Experiment.plot_windrose(pcr.historical_database.site_weather_data('wind_direction_in_deg'), pcr.historical_database.site_weather_data('wind_speed_m_per_s'))
    # Experiment.plot_windrose(prospective_site_weather_data('wind_direction_in_deg'), prospective_site_weather_data('wind_speed_m_per_s'))
    # plt.show()

    # pcr.plot()


# python -m cProfile -o pg.prof sites/prospective_grenoble.py
# snakeviz pg.prof
#
# pip3.11 install line_profiler
# python3.11 -m kernprof -l -v sites/model_h358.py
