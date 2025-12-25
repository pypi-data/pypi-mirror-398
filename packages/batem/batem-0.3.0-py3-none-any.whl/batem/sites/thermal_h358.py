"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
from core.thermal import CAUSALITY, ThermalNetwork
from core.components import SIDE_TYPES, LayeredWallSide, BlockWallSide
from core.model import _CoreModelMaker
from core.data import DataProvider
from sites.data_h358 import generate_h358_data_provider
import matplotlib.pyplot as plt


dp: DataProvider = generate_h358_data_provider(starting_stringdate='15/02/2015', ending_stringdate='15/02/2016')
h358_state_model_maker: _CoreModelMaker = _CoreModelMaker('office', 'corridor', 'downstairs', data_provider=dp)


# corridor wall
door_surface: float = 80e-2 * 200e-2
door: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'corridor', SIDE_TYPES.DOOR, door_surface)
door.layer('wood', 5e-3)
door.layer('air', 15e-3)
door.layer('wood', 5e-3)

glass_surface = 100e-2 * 100e-2
glass: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'corridor', SIDE_TYPES.GLAZING, glass_surface)
glass.layer('glass', 4e-3)

internal_wall_thickness = 13e-3 + 34e-3 + 13e-3
cupboard_corridor_surface: float = (185e-2 + internal_wall_thickness + 34e-2 + 20e-3) * 2.5
corridor_wall_surface: float = (408e-2 + 406e-2 + internal_wall_thickness) * 2.5 - door_surface - glass_surface - cupboard_corridor_surface

cupboard: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'corridor', SIDE_TYPES.WALL, cupboard_corridor_surface)
cupboard.layer('plaster', 13e-3)
cupboard.layer('foam', 34e-3)
cupboard.layer('plaster', 13e-3)
cupboard.layer('air', 50e-2 - 20e-3)
cupboard.layer('wood', 20e-3)

plain_corridor_wall: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'corridor', SIDE_TYPES.WALL, corridor_wall_surface)
plain_corridor_wall.layer('plaster', 13e-3)
plain_corridor_wall.layer('foam', 34e-3)
plain_corridor_wall.layer('plaster', 13e-3)

# outdoor wall
west_glass_surface: float = 2 * 130e-2 * 52e-2 + 27e-2 * 52e-2 + 72e-2 * 52e-2
east_glass_surface: float = 36e-2 * 56e-2
windows_surface: float = west_glass_surface + east_glass_surface
nocavity_surface: float = (685e-2 - 315e-2 - 60e-2) * 2.5 - east_glass_surface
cavity_surface: float = 315e-2 * 2.5 - west_glass_surface

windows: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'outdoor', SIDE_TYPES.WALL, windows_surface)
windows.layer('glass', 4e-3)
windows.layer('air', 12e-3)
windows.layer('glass', 4e-3)

plain_wall: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'outdoor', SIDE_TYPES.WALL, nocavity_surface)
plain_wall.layer('concrete', 30e-2)

cavity_wall: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'outdoor', SIDE_TYPES.WALL, cavity_surface)
cavity_wall.layer('concrete', 30e-2)
cavity_wall.layer('air', 34e-2)
cavity_wall.layer('wood', 20e-3)

# slab
slab_effective_thickness = 11.9e-2
slab_surface = (309e-2 + 20e-3 + 34e-2) * (406e-2 + internal_wall_thickness) + 408e-2 * (273e-2 - 60e-2) - 315e-2 * (34e-2 + 20e-3) - (185e-3 + internal_wall_thickness) * 50e-2
slab: LayeredWallSide = h358_state_model_maker.layered_wall_side('office', 'downstairs', SIDE_TYPES.WALL, slab_surface)
slab.layer('concrete', slab_effective_thickness)
bridge: BlockWallSide = h358_state_model_maker.block_wall_side('office', 'outdoor', SIDE_TYPES.BRIDGE, 0.5 * 0.99, 685e-2)  # ThBAT booklet 5, 3.1.1.2, 22B)


net = ThermalNetwork()
net.T('Tcor', CAUSALITY.IN)
net.T('Tout', CAUSALITY.IN)
net.T('Tin', CAUSALITY.OUT)
net.T('Tslab')
net.T('Tdown', CAUSALITY.IN)
net.HEAT('Tin', 'Pheat')

net.R('Tcor', 'Tin', 'Rcor', val=h358_state_model_maker.wall_resistances('corridor', 'office'))
net.C('Tslab', 'Ci', val=h358_state_model_maker.wall_global_capacitances('downstairs', 'office'))
net.R('Tin', 'Tslab', 'Ri', val=h358_state_model_maker.wall_resistances('downstairs', 'office')/2)
net.R('Tslab', 'Tdown', 'Ri', val=h358_state_model_maker.wall_resistances('downstairs', 'office')/2)
net.R('Tin', 'Tout', 'Rout', val=h358_state_model_maker.wall_resistances('office', 'outdoor'))

print(h358_state_model_maker)
net.draw()

state_model = net.state_model()
print(state_model)
plt.show()
