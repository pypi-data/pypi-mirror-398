from someip_py.codec import *


class AvailableCustomersType(SomeIpPayload):

    Gid: SomeIpDynamicSizeString

    Auth: Uint8

    RouteNumLimit: Uint16

    RouteLengthLimit: Uint16

    def __init__(self):

        self.Gid = SomeIpDynamicSizeString()

        self.Auth = Uint8()

        self.RouteNumLimit = Uint16()

        self.RouteLengthLimit = Uint16()


class IdtCustomerKls(SomeIpPayload):
    _has_dynamic_size = True

    Gid: SomeIpDynamicSizeString

    Auth: Uint8

    RouteNumLimit: Uint16

    RouteLengthLimit: Uint16

    AvailableCustomersSeN: SomeIpDynamicSizeArray[AvailableCustomersType]

    def __init__(self):

        self.Gid = SomeIpDynamicSizeString()

        self.Auth = Uint8()

        self.RouteNumLimit = Uint16()

        self.RouteLengthLimit = Uint16()

        self.AvailableCustomersSeN = SomeIpDynamicSizeArray(AvailableCustomersType)


class IdtCustomer(SomeIpPayload):

    IdtCustomer: IdtCustomerKls

    def __init__(self):

        self.IdtCustomer = IdtCustomerKls()


class IdtRet(SomeIpPayload):

    IdtRet: Uint8

    def __init__(self):

        self.IdtRet = Uint8()
