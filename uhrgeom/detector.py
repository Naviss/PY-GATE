from typing import Any, List, Optional

import opengate as gate

mm = gate.g4_units.mm


class UhrVolume:
    length: float
    width: float
    height: float
    material: str
    repeat: Optional[List[Any]] = None
    repeat_offset: Optional[List[Any]] = None
    opacity: float = 0.5
    color: List[float] = [0, 0, 1]

    def __init__(self, name, mother=None):
        self.name = name
        self.mother = mother

    def get_volume(self) -> gate.geometry.volumes.BoxVolume:
        volume = gate.geometry.volumes.BoxVolume(name=self.name)
        volume.size = [
            self.length,
            self.width,
            self.height,
        ]
        volume.material = self.material
        volume.color = [
            self.color[0],
            self.color[1],
            self.color[2],
            self.opacity,
        ]

        if self.mother is not None:
            volume.mother = self.mother
        else:
            volume.mother = "world"

        if self.repeat:
            volume.repeat = gate.geometry.utility.repeat_array(
                volume.name, self.repeat, self.repeat_offset
            )

        return volume


class Crystal(UhrVolume):
    length = 12 * mm
    width = 1.1225 * mm
    height = 1.1225 * mm
    material = "LYSO"
    repeat = [1, 4, 8]
    repeat_offset = [0, 1.2 * mm, 1.2 * mm]
    opacity = 0.5
    color = [0, 0, 1]


class Matrix(UhrVolume):
    length = Crystal.length
    width = Crystal.width * 4 + (1.2 * mm - Crystal.width) * 3
    height = Crystal.height * 8 + (1.2 * mm - Crystal.height) * 7
    material = "G4_AIR"
    repeat = [1, 2, 1]
    repeat_offset = [0, 6 * mm, 0]
    opacity = 0.2
    color = [0, 0.5, 0.5]


class Asic(UhrVolume):
    length = Crystal.length
    width = Matrix.width * 2 + Crystal.width + 2 * (1.2 * mm - Crystal.width)
    height = Matrix.height
    material = "G4_AIR"
    repeat = [1, 1, 2]
    repeat_offset = [0, 0, 10.8 * mm]
    opacity = 0.5
    color = [0, 1, 0]


class Detector(UhrVolume):
    length = Asic.length
    width = Asic.width
    height = Asic.height * 2 + Crystal.height + 2 * (1.2 * mm - Crystal.height)
    material = "G4_AIR"
    repeat = [1, 6, 1]
    repeat_offset = [0, 13.2 * mm, 0]
    opacity = 0.5
    color = [1, 0, 0]
