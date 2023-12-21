import opengate as gate
from scipy.spatial.transform import Rotation as R

mm = gate.g4_units.mm
um = gate.g4_units.um
keV = gate.g4_units.keV

TIGE_COLOR = [1, 0, 0, 1]  # Red opaque


TIGE_INNER_RADIUS = 100 * um
TIGE_INNER_LENGTH = 119.38 * mm
TIGE_SHELL_RADIUS = 1.5 * mm
TIGE_SHELL_LENGTH = 123.444 * mm


def addCesiumRode(sim, pos, name, mother, activity=None, n=None):
    assert n is not None or activity is not None, "Either n or activity must be set"

    shell_tige = gate.geometry.volumes.TubsVolume(name="shell_tige")
    shell_tige.rmax = TIGE_SHELL_RADIUS
    shell_tige.rmin = 0
    shell_tige.dz = TIGE_SHELL_LENGTH / 2.0

    inner_tige = gate.geometry.volumes.TubsVolume(name="inner_tige")
    inner_tige.rmax = TIGE_INNER_RADIUS
    inner_tige.rmin = 0
    inner_tige.dz = TIGE_INNER_LENGTH / 2.0

    tige = gate.geometry.volumes.subtract_volumes(shell_tige, inner_tige, new_name=name)
    sim.add_volume(tige)
    tige.rotation = R.from_euler("x", 90, degrees=True).as_matrix()
    tige.translation = pos
    tige.mother = mother
    tige.color = TIGE_COLOR
    tige.material = "Aluminium"

    source = sim.add_source("GenericSource", f"source_{name}")
    if n is not None:
        source.n = n
    elif activity is not None:
        source.activity = activity
    else:
        raise ValueError("Either n or activity must be set")
    source.mother = tige.name
    source.particle = "gamma"
    source.energy.mono = 661.7 * keV
    source.direction.type = "iso"
    source.position.type = "box"
    source.position.size = inner_tige.bounding_box_size
    source.position.confine = tige.name

    return tige
