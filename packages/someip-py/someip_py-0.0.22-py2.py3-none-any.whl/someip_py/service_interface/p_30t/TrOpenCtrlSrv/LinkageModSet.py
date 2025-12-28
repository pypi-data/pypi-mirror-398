from someip_py.codec import *


class IdtModeSetKls(SomeIpPayload):

    _include_struct_len = True

    OnOff: Uint8

    def __init__(self):

        self.OnOff = Uint8()


class IdtModeSet(SomeIpPayload):

    IdtModeSet: IdtModeSetKls

    def __init__(self):

        self.IdtModeSet = IdtModeSetKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
