from someip_py.codec import *


class MemorySwitchEnableType(SomeIpPayload):

    RouteIDSeN: Uint64

    MemorySwitchSeN: Uint8

    Case: Uint8

    def __init__(self):

        self.RouteIDSeN = Uint64()

        self.MemorySwitchSeN = Uint8()

        self.Case = Uint8()


class IdtMemoryRouteControl(SomeIpPayload):

    IdtMemoryRouteControl: SomeIpDynamicSizeArray[MemorySwitchEnableType]

    def __init__(self):

        self.IdtMemoryRouteControl = SomeIpDynamicSizeArray(MemorySwitchEnableType)
