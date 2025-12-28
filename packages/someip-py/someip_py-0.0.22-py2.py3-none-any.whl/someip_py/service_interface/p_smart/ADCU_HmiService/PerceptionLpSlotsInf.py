from someip_py.codec import *


class VehiclePoint1(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    PositionZSeN: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()

        self.PositionZSeN = Int32()


class APASlot1(SomeIpPayload):
    _has_dynamic_size = True

    SlotIDSeN: Uint32

    SlotStatusSeN: Uint8

    SlotTypeSeN: Uint8

    SlotPointsSeN: SomeIpDynamicSizeArray[VehiclePoint1]

    BlockPointsSeN: SomeIpDynamicSizeArray[VehiclePoint1]

    def __init__(self):

        self.SlotIDSeN = Uint32()

        self.SlotStatusSeN = Uint8()

        self.SlotTypeSeN = Uint8()

        self.SlotPointsSeN = SomeIpDynamicSizeArray(VehiclePoint1)

        self.BlockPointsSeN = SomeIpDynamicSizeArray(VehiclePoint1)


class PerceptionLpSlots(SomeIpPayload):

    PerceptionLpSlots: SomeIpDynamicSizeArray[APASlot1]

    def __init__(self):

        self.PerceptionLpSlots = SomeIpDynamicSizeArray(APASlot1)
