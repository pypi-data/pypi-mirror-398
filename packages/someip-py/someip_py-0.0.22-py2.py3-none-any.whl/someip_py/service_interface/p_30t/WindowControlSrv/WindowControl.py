from someip_py.codec import *


class IdtWinTrgSrc(SomeIpPayload):

    IdtWinTrgSrc: Uint8

    def __init__(self):

        self.IdtWinTrgSrc = Uint8()


class IdtWindowControlCmd(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowCmd: Uint8

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowCmd = Uint8()


class IdtWindowCommand(SomeIpPayload):

    IdtWindowCommand: SomeIpDynamicSizeArray[IdtWindowControlCmd]

    def __init__(self):

        self.IdtWindowCommand = SomeIpDynamicSizeArray(IdtWindowControlCmd)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
