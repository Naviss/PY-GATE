import argparse
import logging
import multiprocessing as mp
from datetime import datetime

import opengate as gate
from rich.console import Console
from scipy.spatial.transform import Rotation as R

today = datetime.now()
date = today.strftime("%y%m%d-%Hh%M")

console = Console()

parser = argparse.ArgumentParser()
parser.add_argument(
    "-v", "--visu", action="store_true", help="Visualize", default=False
)
parser.add_argument("-t", "--time", type=float, help="time")
parser.add_argument("-T", "--threads", type=int, help="threads", default=1)
parser.add_argument("-r", "--random", type=int, help="random seed", default=20231205)
parser.add_argument(
    "-o", "--output", type=str, help="output file", default=f"sim-{date}.root"
)
args = parser.parse_args()

# Get max number of threads possible on the machine
max_threads = mp.cpu_count()
assert (
    args.threads <= max_threads - 2
), f"Number of threads must be <= {max_threads - 2}"

cm = gate.g4_units.cm
mm = gate.g4_units.mm
um = gate.g4_units.um
m = gate.g4_units.m
Bq = gate.g4_units.Bq
keV = gate.g4_units.keV
sec = gate.g4_units.s

sim = gate.Simulation()
sim.volume_manager.add_material_database("materials.db")

ui = sim.user_info
ui.verbose_level = logging.INFO
ui.running_verbose_level = logging.DEBUG
ui.g4_verbose = False
ui.g4_verbose_level = 1
ui.visu_type = "vrml"
ui.visu = args.visu
ui.visu_verbose = True
ui.random_engine = "MersenneTwister"
ui.random_seed = args.random
ui.number_of_threads = args.threads
console.print(ui)


vol = sim.add_volume("Box", "vol")
vol.material = "G4_AIR"
vol.mother = "world"
vol.size = [150 * cm, 30 * cm, 30 * cm]

lp2Module = sim.add_volume("Box", "lp2Module")
lp2Module.material = "G4_AIR"
lp2Module.size = [12 * mm, 10.86 * mm, 20.46 * mm]
lp2Module.color = [0, 1, 0, 1]
lp2Module.mother = "vol"
lp2Module.repeat = gate.geometry.utility.repeat_array(
    "lp2Module", [1, 6, 1], [0, 13.2 * mm, 0]
)

lp2Matrix = sim.add_volume("Box", "lp2Matrix")
lp2Matrix.material = "G4_AIR"
lp2Matrix.size = [12 * mm, 4.86 * mm, 9.66 * mm]
lp2Matrix.color = [0, 1, 0, 1]
lp2Matrix.mother = "lp2Module"
lp2Matrix.repeat = gate.geometry.utility.repeat_array(
    "lp2Matrix", [1, 2, 2], [0, 6 * mm, 10.8 * mm]
)

lp2Crystal = sim.add_volume("Box", "lp2Crystal")
lp2Crystal.material = "LYSO"
lp2Crystal.size = [12 * mm, 1.1225 * mm, 1.1225 * mm]
lp2Crystal.mother = "lp2Matrix"
lp2Crystal.repeat = gate.geometry.utility.repeat_array(
    "lp2Crystal", [1, 4, 8], [0, 1.2 * mm, 1.2 * mm]
)
lp2Crystal.color = [0, 0, 1, 1]

shell_tige = gate.geometry.volumes.TubsVolume(name="shell_tige")
shell_tige.rmax = 1.5 * mm
shell_tige.rmin = 0
shell_tige.dz = 123.444 * mm / 2.0

inner_tige = gate.geometry.volumes.TubsVolume(name="inner_tige")
inner_tige.rmax = 100 * um
inner_tige.rmin = 0
inner_tige.dz = 119.38 * mm / 2.0

tige = gate.geometry.volumes.subtract_volumes(shell_tige, inner_tige, new_name="tige")
sim.add_volume(tige)
tige.rotation = R.from_euler("x", 90, degrees=True).as_matrix()
tige.translation = [7.5, 0, 0]
tige.mother = "vol"
tige.color = [1, 0, 0, 1]
tige.material = "Plastic"

source = sim.add_source("GenericSource", "source")
if args.visu:
    source.n = 15
else:
    source.activity = 37 * 1000000 * Bq
source.mother = "tige"
source.particle = "gamma"
source.energy.mono = 661.7 * keV
source.direction.type = "iso"
source.position.type = "box"
source.position.size = inner_tige.bounding_box_size
source.position.confine = "tige"

sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option4"
sim.physics_manager.set_production_cut("world", "all", 1 * m)

s = sim.add_actor("SimulationStatisticsActor", "Stats")
s.track_types_flag = True

hc = sim.add_actor("DigitizerHitsCollectionActor", "Hits")
hc.mother = "lp2Crystal"
hc.output = args.output
hc.attributes = [
    "PostPosition",
    "TotalEnergyDeposit",
    "PreStepUniqueVolumeID",
    "GlobalTime",
]

# singles collection
sc = sim.add_actor("DigitizerAdderActor", "Singles")
sc.input_digi_collection = "Hits"
# sc.policy = "EnergyWinnerPosition"
sc.policy = "EnergyWeightedCentroidPosition"
sc.output = hc.output

if args.time is not None:
    sim.run_timing_intervals = [[0, args.time * sec]]

sim.run()

stats = sim.output.get_actor("Stats")
single = sim.output.get_actor("Singles")
console.print(stats)
console.print(single)
