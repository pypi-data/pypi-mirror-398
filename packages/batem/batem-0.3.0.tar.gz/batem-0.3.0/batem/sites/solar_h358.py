"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import matplotlib.pyplot as plt
from batem.core.solar import SolarModel
import batem.core.solar
import batem.core.weather
from pandas.plotting import register_matplotlib_converters
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from batem.core.library import DIRECTIONS_SREF, SLOPES

register_matplotlib_converters()
site_weather_data: batem.core.weather.SiteWeatherData = batem.core.weather.SWDbuilder(
    location='Grenoble', latitude_north_deg=45.19154994547585, longitude_east_deg=5.722065312331381)()
solar_model: SolarModel = batem.core.solar.SolarModel(site_weather_data, distant_masks=[batem.core.solar.SideMask(x_center=10, y_center=10, width=10, height=10, exposure_deg=0, slope_deg=90, elevation=0, normal_rotation_angle_deg=0),])

fig = make_subplots(rows=1, cols=1, shared_xaxes=True)
officeH358_with_mask = batem.core.solar.SolarSystem(solar_model)
batem.core.solar.Collector(officeH358_with_mask, 'main', surface_m2=2, exposure_deg=-13, slope_deg=90, solar_factor=0.85, close_mask=batem.core.solar.RectangularMask((-86, 60), (20, 68), inverted=True))
officeH358_with_mask.day_degrees_solar_gain_xls(
    file_name='officeH358', heat_temperature_reference=21, cool_temperature_reference=26)
global_solar_gains_with_mask = officeH358_with_mask.powers_W(
    gather_collectors=True)
print('total_solar_gain with mask in kWh:',
      sum(global_solar_gains_with_mask)/1000)
# for g in detailed_solar_gains_with_mask:
#     fig.add_trace(go.Scatter(x=officeH358_with_mask.datetimes, y=detailed_solar_gains_with_mask[g], name='%s solar gain with mask in Wh' % g, line_shape='hv'), row=1, col=1)

officeH358_nomask = batem.core.solar.SolarSystem(solar_model)
fig1, ax1 = plt.subplots()
solar_model.plot_heliodon(name='heliodon_obs0', year=2015, observer_elevation_m=0, mask=officeH358_with_mask.collector('main').mask, axes=ax1)
ax1.set_title('Observer elevation: 0m')

fig2, ax2 = plt.subplots()
solar_model.plot_heliodon(name='heliodon_obs5', year=2015, observer_elevation_m=5, mask=officeH358_with_mask.collector('main').mask, axes=ax2)
ax2.set_title('Observer elevation: 5m')

fig3, ax3 = plt.subplots()
solar_model.plot_heliodon(name='heliodon_obs10', year=2015, observer_elevation_m=10, mask=officeH358_with_mask.collector('main').mask, axes=ax3)
ax3.set_title('Observer elevation: 10m')

batem.core.solar.Collector(officeH358_nomask, 'window', surface_m2=2, exposure_deg=-13, slope_deg=90, solar_factor=0.85, close_mask=None)
global_solar_gains_without_mask = officeH358_nomask.powers_W(gather_collectors=True)
print('total_solar_gain without mask in kWh:',
      sum(global_solar_gains_without_mask)/1000)
# for g in detailed_solar_gains_without_mask:
#     fig.add_trace(go.Scatter(x=officeH358_nomask.datetimes, y=detailed_solar_gains_without_mask[g], name='%s solar gain without mask in Wh' % g, line_shape='hv'), row=1, col=1)
# fig.update_layout(title="total heat gain", xaxis_title="date & time (each hour)", yaxis_title="collected heat in Wh")
# fig.show()
e
# test of the solar collector
register_matplotlib_converters()
site_weather_data = batem.core.weather.SWDbuilder(location='Grenoble', latitude_north_deg=45.19154994547585, longitude_east_deg=5.722065312331381)(from_stringdate='01/01/2005', to_stringdate='01/01/2006', albedo=.1)

# solar_model.plot_solar_cardinal_irradiations()

tests = ((DIRECTIONS_SREF.SOUTH, SLOPES.VERTICAL), (DIRECTIONS_SREF.NORTH, SLOPES.VERTICAL), (DIRECTIONS_SREF.EAST, SLOPES.VERTICAL), (DIRECTIONS_SREF.WEST, SLOPES.VERTICAL), (DIRECTIONS_SREF.SOUTH, SLOPES.HORIZONTAL_UP),
         (DIRECTIONS_SREF.NORTH, SLOPES.HORIZONTAL_UP), (DIRECTIONS_SREF.EAST, SLOPES.HORIZONTAL_UP), (DIRECTIONS_SREF.WEST, SLOPES.HORIZONTAL_UP), (DIRECTIONS_SREF.SOUTH, SLOPES.HORIZONTAL_DOWN),)

solar_system = batem.core.solar.SolarSystem(solar_model)
for test in tests:
    print(test)
    exposure_deg, slope_deg = test
    batem.core.solar.Collector(solar_system, exposure_deg.name+'|'+slope_deg.name, surface_m2=1.6, exposure_deg=exposure_deg.value, slope_deg=slope_deg.value, solar_factor=.2)

fig = make_subplots(rows=1, cols=1, shared_xaxes=True)
phis = solar_system.powers_W()
for test in tests:
    collector_name = test[0].name + '|' + test[1].name
    print("Collected Energy on %s: %.2fkWh about %.2f€" % (collector_name,
          sum(phis[collector_name])/1000, sum(phis[collector_name])/1000*.2))
    fig.add_trace(go.Scatter(x=solar_model.site_weather_data.datetimes, y=phis[collector_name], name=collector_name, line_shape='hv'), row=1, col=1)

fig.update_layout(title="total heat gain",
                  xaxis_title="date & time (each hour)", yaxis_title="collected heat in Wh")
fig.show()
plt.show()
# solar_model.plot_angles()
# solar_model.plot_heliodon(2015, 'heliodon')
# plt.show()
