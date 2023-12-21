from dataclasses import dataclass
from typing import Any, List, Optional

import opengate as gate
from scipy.spatial.transform import Rotation as R

mm = gate.g4_units.mm
um = gate.g4_units.um
keV = gate.g4_units.keV

TIGE_COLOR = [1, 0, 0, 1]  # Red opaque


@dataclass
class HollowRode:
    inner_radius: float = 100 * um
    inner_length: float = 119.38 * mm
    shell_radius: float = 1.5 * mm
    shell_length: float = 123.444 * mm

    def __init__(self, name: str, mother: str):
        self.name = name
        self.mother = mother

    def get_volume(self):
        shell_tige = gate.geometry.volumes.TubsVolume(name="shell_tige")
        shell_tige.rmax = self.shell_radius
        shell_tige.rmin = 0
        shell_tige.dz = self.shell_length / 2.0
        shell_tige.rotation = R.from_euler("x", 90, degrees=True).as_matrix()

        inner_tige = gate.geometry.volumes.TubsVolume(name="inner_tige")
        inner_tige.rmax = self.inner_radius
        inner_tige.rmin = 0
        inner_tige.dz = self.inner_length / 2.0
        inner_tige.rotation = R.from_euler("x", 90, degrees=True).as_matrix()

        tige = gate.geometry.volumes.subtract_volumes(
            shell_tige, inner_tige, new_name=self.name
        )
        tige.mother = self.mother
        tige.color = TIGE_COLOR
        tige.material = "Aluminium"

        return tige


@dataclass
class CesiumSource:
    def __init__(
        self,
        sim: gate.Simulation,
        name: str,
        mother: str,
        phantom: Any,
        pos: List[float],
        activity: Optional[float] = None,
        n: Optional[int] = None,
    ):
        self.name = name
        self.mother = mother
        self.phantom = phantom
        self.pos = pos
        self.activity = activity
        self.n = n

        self.phantom_volume = self.phantom.get_volume()
        self.phantom_volume.translation = self.pos
        sim.add_volume(self.phantom_volume)

        self.source = sim.add_source("GenericSource", self.name)

        # n xor activity
        assert (self.n is None and self.activity is not None) or (
            self.n is not None and self.activity is None
        ), "Either n or activity must be set"
        if self.n is not None:
            self.source.n = self.n
        else:
            self.source.activity = self.activity

        self.source.mother = self.mother
        self.source.particle = "gamma"
        self.source.energy.mono = 661.7 * keV
        self.source.direction.type = "iso"
        self.source.position.type = "box"
        self.source.position.size = self.phantom_volume.bounding_box_size
        self.source.position.confine = self.phantom_volume.name
