import argparse
import logging
import multiprocessing as mp
from datetime import datetime
from operator import add

import opengate as gate
from rich.console import Console

import utils
from phantom.hollow_rode import CesiumSource, HollowRode
from uhrgeom.detector import Asic, Crystal, Detector, Matrix

cm = gate.g4_units.cm
mm = gate.g4_units.mm
m = gate.g4_units.m
Bq = gate.g4_units.Bq
keV = gate.g4_units.keV
sec = gate.g4_units.s

today = datetime.now()
date = today.strftime("%y%m%d-%Hh%M")

console = Console()

parser = argparse.ArgumentParser()
visu_option = parser.add_mutually_exclusive_group()
visu_option.add_argument(
    "-v", "--visu", action="store_true", help="Visualize", default=False
)
visu_option.add_argument("-w", "--wrl", type=str, help="VRML file")
parser.add_argument("-t", "--time", type=float, help="time")
parser.add_argument("-T", "--threads", type=int, help="threads", default=1)
parser.add_argument(
    "-d", "--distance", type=float, help="Distance source crystal", default=0.0
)
parser.add_argument("-m", "--margin", type=int, help="World margin in mm", default=10)
parser.add_argument("-r", "--random", type=int, help="random seed", default=20231205)
parser.add_argument(
    "-o", "--output", type=str, help="output file", default=f"data/sim-{date}.root"
)
args = parser.parse_args()

# Get max number of threads possible on the machine
max_threads = mp.cpu_count()
assert (
    args.threads <= max_threads - 2
), f"Number of threads must be <= {max_threads - 2}"


sim = gate.Simulation()
sim.volume_manager.add_material_database("materials.db")

if args.time is not None:
    sim.run_timing_intervals = [[0, args.time * sec]]

# Set user info configs
ui = sim.user_info

# UI: Verbosity
ui.verbose_level = logging.INFO
ui.running_verbose_level = logging.DEBUG
ui.g4_verbose = False
ui.g4_verbose_level = 1

# UI: GUI
if args.visu or args.wrl is not None:
    ui.visu = True
    if args.visu:
        ui.visu_type = "vrml"
    if args.wrl is not None:
        ui.visu_type = "vrml_file_only"
        ui.visu_filename = args.wrl
    ui.visu_verbose = True

# UI: Random configs
ui.random_engine = "MersenneTwister"
ui.random_seed = args.random

# UI: Threads
ui.number_of_threads = args.threads
console.print(ui)

world = sim.world
world.material = "G4_AIR"

vol = sim.add_volume("Box", "vol")
vol.material = "G4_AIR"
vol.mother = "world"
vol.size = world.size

lp2Detector = Detector("lp2Detector", vol.name)
sim.add_volume(lp2Detector.get_volume())

lp2Asic = Asic("lp2Asic", lp2Detector.name)
sim.add_volume(lp2Asic.get_volume())

lp2Matrix = Matrix("lp2Matrix", lp2Asic.name)
sim.add_volume(lp2Matrix.get_volume())

lp2Crystal = Crystal("lp2Crystal", lp2Matrix.name)
sim.add_volume(lp2Crystal.get_volume())

if args.visu:
    events = {"n": 15}
else:
    events = {"activity": 37.0 * 1e6 * Bq}

tige1 = HollowRode("tige1", vol.name)
tige2 = HollowRode("tige2", vol.name)

s1 = CesiumSource(
    sim,
    "source_tige1",
    tige1.name,
    tige1,
    [lp2Detector.length + args.distance * mm, 0, 1.5 * mm],
    **events,
)

s2 = CesiumSource(
    sim,
    "source_tige2",
    tige2.name,
    tige2,
    [lp2Detector.length + args.distance * mm, 0, -1.5 * mm],
    **events,
)

console.print("Checking volumes...")


console.print("Updating world size...")
volMax = utils.compute_max_bbox_for_child(sim, vol.name)
newVolSize = list(
    map(add, volMax, [args.margin * mm, args.margin * mm, args.margin * mm])
)
vol.size = newVolSize

newWorldSize = list(map(add, newVolSize, [10.0 * mm, 10.0 * mm, 10.0 * mm]))
world.size = newWorldSize


sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option4"
sim.physics_manager.set_production_cut("world", "all", 1 * m)

s = sim.add_actor("SimulationStatisticsActor", "Stats")
s.track_types_flag = True

hc = sim.add_actor("DigitizerHitsCollectionActor", "Hits")
hc.mother = lp2Crystal.name
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
sc.policy = "EnergyWeightedCentroidPosition"
sc.output = hc.output
sc.group_volume = lp2Asic.name

sim.run()

stats = sim.output.get_actor("Stats")
single = sim.output.get_actor("Singles")
console.print(stats)
console.print(single)
