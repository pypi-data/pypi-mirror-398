from someip_py.codec import *


class CoordinateSys(SomeIpPayload):

    CoordinateXSeN: Int32

    CoordinateYSeN: Int32

    CoordinateZSeN: Int32

    def __init__(self):

        self.CoordinateXSeN = Int32()

        self.CoordinateYSeN = Int32()

        self.CoordinateZSeN = Int32()


class IdtNavigationTargetKls(SomeIpPayload):

    NavigationTargetTypeSeN: Uint8

    NavigationTargetSlotIdSeN: Uint32

    NavigationTargetPointSeN: CoordinateSys

    NavigationPOIIDSeN: Uint32

    AVPSelectedSlotId: Uint32

    def __init__(self):

        self.NavigationTargetTypeSeN = Uint8()

        self.NavigationTargetSlotIdSeN = Uint32()

        self.NavigationTargetPointSeN = CoordinateSys()

        self.NavigationPOIIDSeN = Uint32()

        self.AVPSelectedSlotId = Uint32()


class IdtNavigationTarget(SomeIpPayload):

    IdtNavigationTarget: IdtNavigationTargetKls

    def __init__(self):

        self.IdtNavigationTarget = IdtNavigationTargetKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
