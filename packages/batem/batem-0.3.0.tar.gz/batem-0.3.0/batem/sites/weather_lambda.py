"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
import time
from core.lambdahouse import ReportGenerator, Analyzes, DefaultConfiguration


location = 'Grenoble'
weather_year = 2023
latitude, longitude = 45.19154994547585, 5.722065312331381

configuration = DefaultConfiguration(location, latitude=latitude, longitude=longitude, weather_year=weather_year)
tini = time.time()
experiment = ReportGenerator(configuration, on_screen=False)
analysis = Analyzes(experiment)
analysis.climate(experiment)
analysis.evolution(experiment)
experiment.close()
print('duration: %i minutes' % (int(round((time.time() - tini) / 60))))
