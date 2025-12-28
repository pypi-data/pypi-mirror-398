from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class IdtNavigationDistreqKls(SomeIpPayload):

    NavigationDistreqname: SomeIpDynamicSizeString

    NavigationDistpiont: Pos2D

    NavigationStartreqname: SomeIpDynamicSizeString

    NavigationStartpiont: Pos2D

    IsNavigationDistpiont: Uint8

    def __init__(self):

        self.NavigationDistreqname = SomeIpDynamicSizeString()

        self.NavigationDistpiont = Pos2D()

        self.NavigationStartreqname = SomeIpDynamicSizeString()

        self.NavigationStartpiont = Pos2D()

        self.IsNavigationDistpiont = Uint8()


class IdtNavigationDistreq(SomeIpPayload):

    IdtNavigationDistreq: IdtNavigationDistreqKls

    def __init__(self):

        self.IdtNavigationDistreq = IdtNavigationDistreqKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
