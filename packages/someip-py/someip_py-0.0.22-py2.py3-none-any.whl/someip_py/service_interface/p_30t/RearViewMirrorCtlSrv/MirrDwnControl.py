from someip_py.codec import *


class IdtMirrDwnCtlCmd(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrDwnCmd: Uint8

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrDwnCmd = Uint8()


class IdtMirrDwnCommand(SomeIpPayload):

    IdtMirrDwnCommand: SomeIpDynamicSizeArray[IdtMirrDwnCtlCmd]

    def __init__(self):

        self.IdtMirrDwnCommand = SomeIpDynamicSizeArray(IdtMirrDwnCtlCmd)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
