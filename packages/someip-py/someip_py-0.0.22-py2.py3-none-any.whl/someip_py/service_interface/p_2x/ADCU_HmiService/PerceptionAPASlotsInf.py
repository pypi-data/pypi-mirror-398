from someip_py.codec import *


class VehiclePoint(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()


class APASlot(SomeIpPayload):
    _has_dynamic_size = True

    SlotIDSeN: Uint32

    SlotStatusSeN: Uint8

    SlotTypeSeN: Uint8

    SlotPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    BlockPointsSeN: SomeIpDynamicSizeArray[VehiclePoint]

    SlotSelectButtonSeN: Uint8

    ApaChargeSlotSeN: Uint8

    ApaChargeSlotNum: SomeIpDynamicSizeArray[Int8]

    ApaReqReleaseLockCard: Uint8

    SlotSizeTypeSeN: Uint8

    SlotCollectedStatusSeN: Uint8

    def __init__(self):

        self.SlotIDSeN = Uint32()

        self.SlotStatusSeN = Uint8()

        self.SlotTypeSeN = Uint8()

        self.SlotPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.BlockPointsSeN = SomeIpDynamicSizeArray(VehiclePoint)

        self.SlotSelectButtonSeN = Uint8()

        self.ApaChargeSlotSeN = Uint8()

        self.ApaChargeSlotNum = SomeIpDynamicSizeArray(Int8)

        self.ApaReqReleaseLockCard = Uint8()

        self.SlotSizeTypeSeN = Uint8()

        self.SlotCollectedStatusSeN = Uint8()


class PerceptionAPASlots(SomeIpPayload):

    PerceptionAPASlots: SomeIpDynamicSizeArray[APASlot]

    def __init__(self):

        self.PerceptionAPASlots = SomeIpDynamicSizeArray(APASlot)
