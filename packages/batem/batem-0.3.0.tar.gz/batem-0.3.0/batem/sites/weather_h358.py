"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import batem.core.weather
import batem.core.solar
import batem.core.timemg
import plotly.graph_objects as go
from datetime import datetime


def plot_rain_events(datetimes: list[datetime], precipitations: list[float], ax=None):
    if ax is None:
        # Matplotlib functionality removed - use Plotly instead
        return None
    days_with_rain: list[str] = list()
    days: list[str] = list()
    rains_dict: dict[tuple[float, float], int] = dict()
    rains_months_dict: dict[tuple[float, float], list[str]] = dict()
    rain_duration: int = 0
    max_duration = 0
    rain_quantity: float = 0
    max_quantity = 0
    threshold = 0.1
    was_raining = False
    for k, precipitation in enumerate(precipitations):
        stringdate = batem.core.timemg.datetime_to_stringdate(
            datetimes[k]).split(' ')[0]
        if stringdate not in days:
            days.append(stringdate)
        if was_raining and precipitation > 0:  # ongoing rain event
            rain_duration += 1
            rain_quantity += precipitation
            if stringdate not in days_with_rain:
                days_with_rain.append(stringdate)
        elif was_raining and precipitation == 0:  # end of rain event
            characteristics: tuple[int, int] = (
                rain_duration, round(10*rain_quantity/rain_duration)/10)
            max_duration: int = max(max_duration, characteristics[0])
            max_quantity: int = max(max_quantity, characteristics[1])
            month = datetimes[k].month
            if characteristics in rains_dict:
                rains_dict[characteristics] += 1
                if str(month) not in rains_months_dict[characteristics]:
                    rains_months_dict[characteristics].append(str(month))
            else:
                rains_dict[characteristics] = 1
                rains_months_dict[characteristics] = [str(month)]
            was_raining = False
            rain_duration = 0
            rain_quantity = 0
        elif not was_raining and precipitation > threshold:  # beginning of rain event
            if stringdate not in days_with_rain:
                days_with_rain.append(stringdate)
            rain_duration = 1
            rain_quantity = precipitation
            was_raining = True

    ax.set(xlim=(0, max_duration), ylim=(0, max_quantity))
    for characteristics in rains_dict:
        # Matplotlib functionality removed - would need Plotly equivalent
        pass
    ax.set_title('rain events (numbers stands for month# (%i raining days out of %i)' % (
        len(days_with_rain), len(days)))
    ax.set_xlabel('duration in hours')
    ax.set_ylabel('quantity in mm')


site_weather_data = batem.core.weather.SWDbuilder().build(
    location='grenoble',
    latitude_north_deg=45.19154994547585,
    longitude_east_deg=5.722065312331381,
    from_requested_stringdate='1/01/2019',
    to_requested_stringdate='1/01/2020'
    )

solar_model = batem.core.solar.SolarModel(site_weather_data)
solar_model.match_measurements(plot=False)

irradiances_detailed = solar_model.irradiances_W(exposure_deg=0, slope_deg=180, with_details=True)

# Create Plotly plot for weather data overview
weather_fig = go.Figure()

# Add weather data traces
weather_fig.add_trace(
    go.Scatter(
        x=site_weather_data.get('datetime'),
        y=site_weather_data.get('direct_radiation'),
        name='Direct Radiation (Weather)',
        line=dict(color='orange', width=2),
        hovertemplate='<b>Direct</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

weather_fig.add_trace(
    go.Scatter(
        x=site_weather_data.get('datetime'),
        y=site_weather_data.get('dhi'),
        name='Diffuse HorizontalRadiation (Weather)',
        line=dict(color='lightblue', width=2),
        hovertemplate='<b>Diffuse</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

weather_fig.add_trace(
    go.Scatter(
        x=site_weather_data.get('datetime'),
        y=site_weather_data.get('dni'),
        name='Direct Normal Irradiance (Weather)',
        line=dict(color='red', width=2),
        hovertemplate='<b>DNI</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

# Update layout for weather data plot
weather_fig.update_layout(
    title={
        'text': 'Weather Data - Solar Irradiance Components',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 16}
    },
    xaxis_title='Date',
    yaxis_title='Irradiance (W/m²)',
    height=500,
    hovermode='x unified',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=30, label="30d", step="day", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    )
)

weather_fig.show()
# - 90 east, 90 west, 0 south, 180 north (clockwise with South as reference)
exposure = 0
slope = 180  # 0 facing the ground, 90 vertical, 180 facing the sky
# , mask=buildingenergy.solar.RectangularMask(minmax_azimuths_deg=(-90+exposure, 90+exposure), minmax_altitudes_deg=(-90+slope, 90+slope))
irradiances_detailed = solar_model.irradiances_W(exposure_deg=exposure, slope_deg=slope, with_details=True)

print('openmeteo (direct): %f' % (sum(site_weather_data.get('direct_radiation'))/1000))
print('calculus: %f' % (sum(irradiances_detailed[batem.core.solar.COLLECTED_RADIATIONS.NORMAL])/1000))

# Create interactive Plotly plot

# Create subplot with secondary y-axis for better visualization
# fig = make_subplots(
#     rows=1, cols=1,
#     subplot_titles=('Solar Irradiance Components', 'Weather Data Comparison'),
#     vertical_spacing=0.1,
#     row_heights=[0.7, 0.3]
# )

fig = go.Figure()

# Get datetime data
datetimes = site_weather_data.get('datetime')

# Add irradiance components to first subplot
fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=irradiances_detailed[batem.core.solar.COLLECTED_RADIATIONS.TILT_DIRECT],
        name='Model DNI',
        line=dict(color='orange', dash='dash', width=1),
        hovertemplate='<b>Direct</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=irradiances_detailed[batem.core.solar.COLLECTED_RADIATIONS.TILT_DIFFUSE],
        name='Model DHI',
        line=dict(color='blue', dash='dash', width=1),
        hovertemplate='<b>Diffuse</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=irradiances_detailed[batem.core.solar.COLLECTED_RADIATIONS.TILT_REFLECTED],
        name='Model RHI',
        line=dict(color='brown', dash='dash', width=1),
        hovertemplate='<b>Reflected</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=irradiances_detailed[batem.core.solar.COLLECTED_RADIATIONS.NORMAL],
        name='Model DNI',
        line=dict(color='pink', dash='dash', width=1),
        hovertemplate='<b>Normal</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=irradiances_detailed[batem.core.solar.COLLECTED_RADIATIONS.TILT_TOTAL],
        name='Model GHI',
        line=dict(color='red', dash='dash', width=1),
        hovertemplate='<b>Total</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

# Add weather data comparison in second subplot
fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=site_weather_data.get('ghi'),
        name='Weather GHI',
        line=dict(color='red', width=1),
        hovertemplate='<b>Weather Direct</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=site_weather_data.get('dhi'),
        name='Weather DHI',
        line=dict(color='blue', width=2),
        hovertemplate='<b>Weather Diffuse</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

fig.add_trace(
    go.Scatter(
        x=datetimes,
        y=site_weather_data.get('dni'),
        name='Weather DNI',
        line=dict(color='green', width=2),
        hovertemplate='<b>Weather Normal</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
    )
)

# Update layout
fig.update_layout(
    title={
        'text': 'Solar Irradiance Analysis - Model vs Weather Data',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 18}
    },
    height=800,
    hovermode='x unified',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Update axes
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Irradiance (W/m²)")

# Add range slider for time navigation
fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=30, label="30d", step="day", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    )
)

fig.show()

# Commented out code - can be implemented with Plotly if needed:
# - Solar angles plot (altitude, azimuth over time)
# - Rain events visualization
