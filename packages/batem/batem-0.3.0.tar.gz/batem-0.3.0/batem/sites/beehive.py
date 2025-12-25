# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from __future__ import annotations
from math import pi
import matplotlib.pyplot as plt
from core.library import SIDE_TYPES
from core.thermal import ThermalNetwork, CAUSALITY
from core.solar import SolarModel

from core.model import _CoreModelMaker
from core.data import DataProvider

# we write the interfaces between rooms

height = 34e-2
depth = 50e-2
width = 42.8e-2
external_wood_thickness = 2.4e-2
internal_wall_thickness = 2.1e-2
external_insulation_foam = 1e-2
external_insulation_wood = 2e-2
number_of_rooms = 11
insulation = False


weather_file_name: str = 'Grenoble-INP1990.json'
weather_year: int = 2021
altitude: float = 212
albedo = 0.1
location: str = 'Grenoble'
latitude_north_deg = 45.19154994547585
longitude_east_deg = 5.722065312331381

starting_stringdate = '1/01/%i' % weather_year
ending_stringdate = '1/02/%i' % (weather_year)
dp = DataProvider(location=location, latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg, starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate)
site_weather_data = dp.independent_variable_set.site_weather_data
solar_model = SolarModel(site_weather_data)  # for solar radiation
Touts = site_weather_data.get('temperature')

T_queen = 35
swarm_location = 4
swarm_radius = 10e-2
swarm_equivalent_foam_thickness = 5e-2


def beehive_compute(insulation):
    external_insulation = external_insulation_foam + external_insulation_wood
    effective_height = height-2*(external_wood_thickness+external_insulation)
    effective_depth = depth-2*(external_wood_thickness+external_insulation)
    effective_room_width = (width-2*(external_wood_thickness+external_insulation)-(number_of_rooms-1)*internal_wall_thickness)/(number_of_rooms-1)

    surface_side = effective_height * effective_depth
    surface_room_front = effective_room_width * effective_height
    surface_room_top = effective_room_width * effective_depth

    rooms = ['queen'] + ['e%i' % (i) for i in range(number_of_rooms)]
    beehive = _CoreModelMaker(*rooms, data_provider=dp)

    # left room
    left_room_vertical = beehive.layered_wall_side('outdoor', 'e0', SIDE_TYPES.WALL, surface_side+2*surface_room_front)
    left_room_vertical.layer('wood', external_wood_thickness)
    if insulation:
        left_room_vertical.layer('foam', external_insulation_foam)
        left_room_vertical.layer('wood', external_insulation_wood)

    left_room_horizontal = beehive.layered_wall_side('outdoor', 'e0', SIDE_TYPES.ROOF, 2*surface_room_top)
    left_room_horizontal.layer('wood', external_wood_thickness)
    if insulation:
        left_room_horizontal.layer('foam', external_insulation_foam)
        left_room_horizontal.layer('wood', external_insulation_wood)

    # right room
    right_room_vertical = beehive.layered_wall_side('outdoor', 'e%i' % (number_of_rooms-1), SIDE_TYPES.WALL, surface_side+2*surface_room_front)
    right_room_vertical.layer('wood', external_wood_thickness)
    if insulation:
        right_room_vertical.layer('foam', external_insulation_foam)
        right_room_vertical.layer('wood', external_insulation_wood)

    right_room_horizontal = beehive.layered_wall_side('outdoor', 'e%i' % (number_of_rooms-1), SIDE_TYPES.ROOF, 2*surface_room_top)
    right_room_horizontal.layer('wood', external_wood_thickness)
    if insulation:
        right_room_horizontal.layer('foam', external_insulation_foam)
        right_room_horizontal.layer('wood', external_insulation_wood)

    # internal rooms
    for i in range(number_of_rooms-1):
        internal_room_vertical = beehive.layered_wall_side('outdoor', 'e%i' % i, SIDE_TYPES.WALL, 2*surface_room_front)
        internal_room_vertical.layer('wood', external_wood_thickness)
        if insulation:
            internal_room_vertical.layer('foam', external_insulation_foam)
            internal_room_vertical.layer('wood', external_insulation_wood)

        internal_room_horizontal = beehive.layered_wall_side('outdoor', 'e%i' % i, SIDE_TYPES.ROOF, 2*surface_room_top)
        internal_room_horizontal.layer('wood', external_wood_thickness)
        if insulation:
            internal_room_horizontal.layer('foam', external_insulation_foam)
            internal_room_horizontal.layer('wood', external_insulation_wood)

    for i in range(number_of_rooms-1):
        internal_wall_room = beehive.layered_wall_side('e%i' % i, 'e%i' % (i+1), SIDE_TYPES.WALL, surface_side)
        internal_wall_room.layer('wood', internal_wall_thickness)

    swarm = beehive.layered_wall_side('e%i' % swarm_location, 'queen', SIDE_TYPES.WALL, 4*pi*(swarm_radius)**2)
    swarm.layer('foam', swarm_equivalent_foam_thickness)  # this is an equivalent thickness

    print(beehive)

    net = ThermalNetwork()
    net.T('Tout', CAUSALITY.IN)  # I input the known temperatures
    net.T('Tqueen', CAUSALITY.OUT)

    for i in range(number_of_rooms):
        net.T('T%i' % i, causality=CAUSALITY.OUT)
        net.R(fromT='Tout', toT='T%i' % i, name='Rout%i' % i, val=beehive.wall_resistances('e%i' % i, 'outdoor'))

    for i in range(number_of_rooms-1):
        net.R(fromT='T%i' % i, toT='T%i' % (i+1), name='R%i_%i' % (i, i+1), val=beehive.wall_resistances('e%i' % i, 'e%i' % (i+1)))

    net.R(fromT='T%i' % swarm_location, toT='Tqueen', name='Rswarm', val=beehive.wall_resistances('e%i' % swarm_location, 'queen'))

    net.HEAT(T='Tqueen', name='Pessain')

    state_model = net.state_model()
    print(state_model)

    D = state_model.D

    P_swarm = list()
    T_queen_valid = list()
    Ti = {'T%i' % i: [] for i in range(number_of_rooms)}
    for Tout in Touts:
        P_swarm.append((T_queen - D[0, 0]*Tout) / D[0, 1])
        Y = D[:, 0] * Tout + D[:, 1] * P_swarm[-1]
        T_queen_valid.append(Y[0, 0])
        for i in range(number_of_rooms):
            Ti['T%i' % i].append(Y[i+1, 0])
    return P_swarm, Ti, T_queen_valid


P_swarm_base, Ti_base, T_queen_base = beehive_compute(False)
P_swarm_insulation, Ti_insulation, T_queen_insulation = beehive_compute(True)

plt.subplot(311)
plt.plot(site_weather_data.get('datetime'), Touts, label='Tout')
plt.plot(site_weather_data.get('datetime'), T_queen_base, label='Tqueen')
for i in range(number_of_rooms):
    plt.plot(site_weather_data.get('datetime'), Ti_base['T%i' % i], label='T%i' % i)
plt.legend()
plt.ylabel('base')
plt.subplot(312)
plt.plot(site_weather_data.get('datetime'), Touts, label='Tout')
plt.plot(site_weather_data.get('datetime'), T_queen_insulation, label='Tqueen')
for i in range(number_of_rooms):
    plt.plot(site_weather_data.get('datetime'), Ti_insulation['T%i' % i], label='T%i' % i)
plt.legend()
plt.ylabel('insulation')
plt.subplot(313)
plt.plot(site_weather_data.get('datetime'), P_swarm_base, label='P_swarm_base')
plt.plot(site_weather_data.get('datetime'), P_swarm_insulation, label='P_swarm_insulation')
plt.legend()
plt.show()
