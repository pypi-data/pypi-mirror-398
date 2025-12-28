from someip_py.codec import *


class VehiclePoint(SomeIpPayload):

    PositionXSeN: Int16

    PositionYSeN: Int16

    def __init__(self):

        self.PositionXSeN = Int16()

        self.PositionYSeN = Int16()


class APASlot(SomeIpPayload):
    _has_dynamic_size = True

    SlotIDSeN: Uint32

    SlotStatusSeN: Uint8

    SlotTypeSeN: Uint8

    SlotPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    BlockPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    SlotSelectButtonSeN: Uint8

    SlotSelectDisplaySeN: Uint8

    SlotSizeTypeSeN: Uint8

    def __init__(self):

        self.SlotIDSeN = Uint32()

        self.SlotStatusSeN = Uint8()

        self.SlotTypeSeN = Uint8()

        self.SlotPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.BlockPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.SlotSelectButtonSeN = Uint8()

        self.SlotSelectDisplaySeN = Uint8()

        self.SlotSizeTypeSeN = Uint8()


class PerceptionAPASlots(SomeIpPayload):

    PerceptionAPASlots: SomeIpDynamicSizeArray[APASlot]

    def __init__(self):

        self.PerceptionAPASlots = SomeIpDynamicSizeArray(APASlot)
