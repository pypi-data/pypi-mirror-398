from someip_py.codec import *


class IdtMirrPositionCmdTrgSrc(SomeIpPayload):

    IdtMirrPositionCmdTrgSrc: Uint8

    def __init__(self):

        self.IdtMirrPositionCmdTrgSrc = Uint8()


class IdtMirrPositionCtlCmd(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrXPositionCmd: Uint16

    MirrYPositionCmd: Uint16

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrXPositionCmd = Uint16()

        self.MirrYPositionCmd = Uint16()


class IdtMirrPositionCommand(SomeIpPayload):

    IdtMirrPositionCommand: SomeIpDynamicSizeArray[IdtMirrPositionCtlCmd]

    def __init__(self):

        self.IdtMirrPositionCommand = SomeIpDynamicSizeArray(IdtMirrPositionCtlCmd)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
