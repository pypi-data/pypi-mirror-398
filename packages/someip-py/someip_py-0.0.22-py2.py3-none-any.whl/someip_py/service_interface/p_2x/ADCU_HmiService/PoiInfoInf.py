from someip_py.codec import *


class Pos2D(SomeIpPayload):

    LongitudePos2DSeN: Float64

    LatitudePos2DSeN: Float64

    def __init__(self):

        self.LongitudePos2DSeN = Float64()

        self.LatitudePos2DSeN = Float64()


class ADPoiBasicInfo(SomeIpPayload):

    PoiId: SomeIpDynamicSizeString

    Name: SomeIpDynamicSizeString

    Address: SomeIpDynamicSizeString

    PoiLoc: Pos2D

    Distance: Uint16

    TypeCode: SomeIpDynamicSizeString

    Type: SomeIpDynamicSizeString

    def __init__(self):

        self.PoiId = SomeIpDynamicSizeString()

        self.Name = SomeIpDynamicSizeString()

        self.Address = SomeIpDynamicSizeString()

        self.PoiLoc = Pos2D()

        self.Distance = Uint16()

        self.TypeCode = SomeIpDynamicSizeString()

        self.Type = SomeIpDynamicSizeString()


class ADPoiChildInfo(SomeIpPayload):

    Basic: ADPoiBasicInfo

    PPoiId: SomeIpDynamicSizeString

    RelType: SomeIpDynamicSizeString

    def __init__(self):

        self.Basic = ADPoiBasicInfo()

        self.PPoiId = SomeIpDynamicSizeString()

        self.RelType = SomeIpDynamicSizeString()


class ADPoiInfo(SomeIpPayload):
    _has_dynamic_size = True

    Basic: ADPoiBasicInfo

    Weight: SomeIpDynamicSizeString

    CityAdCode: Int32

    AdCode: Int32

    ChildrenList: SomeIpDynamicSizeArray[ADPoiChildInfo]

    def __init__(self):

        self.Basic = ADPoiBasicInfo()

        self.Weight = SomeIpDynamicSizeString()

        self.CityAdCode = Int32()

        self.AdCode = Int32()

        self.ChildrenList = SomeIpDynamicSizeArray(ADPoiChildInfo)


class IdtPoiInfoKls(SomeIpPayload):
    _has_dynamic_size = True

    TaskId: Uint64

    PoiList: SomeIpDynamicSizeArray[ADPoiInfo]

    def __init__(self):

        self.TaskId = Uint64()

        self.PoiList = SomeIpDynamicSizeArray(ADPoiInfo)


class IdtPoiInfo(SomeIpPayload):

    IdtPoiInfo: IdtPoiInfoKls

    def __init__(self):

        self.IdtPoiInfo = IdtPoiInfoKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
