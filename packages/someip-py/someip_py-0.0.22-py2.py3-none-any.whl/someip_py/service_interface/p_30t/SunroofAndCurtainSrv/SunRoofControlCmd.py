from someip_py.codec import *


class IdtOHCtrlCmdKls(SomeIpPayload):

    _include_struct_len = True

    OHControlCmd: Uint8

    OHCTrgSrc: Uint8

    def __init__(self):

        self.OHControlCmd = Uint8()

        self.OHCTrgSrc = Uint8()


class IdtOHCtrlCmd(SomeIpPayload):

    IdtOHCtrlCmd: IdtOHCtrlCmdKls

    def __init__(self):

        self.IdtOHCtrlCmd = IdtOHCtrlCmdKls()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
