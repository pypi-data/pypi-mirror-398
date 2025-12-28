from someip_py.codec import *


class IdtLocalModelDeviceCode(SomeIpPayload):

    IdtLocalModelDeviceCode: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtLocalModelDeviceCode = SomeIpDynamicSizeString()


class IdtLocalSysDescr(SomeIpPayload):

    IdtLocalSysDescr: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtLocalSysDescr = SomeIpDynamicSizeString()


class IdtLocalSysName(SomeIpPayload):

    IdtLocalSysName: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtLocalSysName = SomeIpDynamicSizeString()


class IdtLocalDviceID(SomeIpPayload):

    IdtLocalDviceID: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtLocalDviceID = SomeIpDynamicSizeString()


class IdtDeviceRegisterLocalResult(SomeIpPayload):

    IdtDeviceRegisterLocalResult: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtDeviceRegisterLocalResult = SomeIpDynamicSizeString()


class IdtDeviceRegisterLocalMessage(SomeIpPayload):

    IdtDeviceRegisterLocalMessage: SomeIpDynamicSizeString

    def __init__(self):

        self.IdtDeviceRegisterLocalMessage = SomeIpDynamicSizeString()
