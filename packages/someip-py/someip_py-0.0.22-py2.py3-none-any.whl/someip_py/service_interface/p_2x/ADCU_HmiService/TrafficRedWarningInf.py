from someip_py.codec import *


class VehiclePoint(SomeIpPayload):

    PositionXSeN: Int32

    PositionYSeN: Int32

    def __init__(self):

        self.PositionXSeN = Int32()

        self.PositionYSeN = Int32()


class TrafficRedWarningSeN(SomeIpPayload):

    TrafficRedWarningID: Uint64

    TrafficRedWarningPointSeN: VehiclePoint

    TimeStamp: Uint64

    def __init__(self):

        self.TrafficRedWarningID = Uint64()

        self.TrafficRedWarningPointSeN = VehiclePoint()

        self.TimeStamp = Uint64()


class TrafficRedWarningInfo(SomeIpPayload):

    TrafficRedWarningInfo: SomeIpDynamicSizeArray[TrafficRedWarningSeN]

    def __init__(self):

        self.TrafficRedWarningInfo = SomeIpDynamicSizeArray(TrafficRedWarningSeN)
