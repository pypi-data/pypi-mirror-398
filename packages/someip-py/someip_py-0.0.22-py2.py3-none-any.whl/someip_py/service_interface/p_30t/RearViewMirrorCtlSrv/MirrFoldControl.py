from someip_py.codec import *


class IdtMirrFoldCmdTrgSrc(SomeIpPayload):

    IdtMirrFoldCmdTrgSrc: Uint8

    def __init__(self):

        self.IdtMirrFoldCmdTrgSrc = Uint8()


class IdtMirrFoldCtlCmd(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrFoldCmd: Uint8

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrFoldCmd = Uint8()


class IdtMirrFoldCommand(SomeIpPayload):

    IdtMirrFoldCommand: SomeIpDynamicSizeArray[IdtMirrFoldCtlCmd]

    def __init__(self):

        self.IdtMirrFoldCommand = SomeIpDynamicSizeArray(IdtMirrFoldCtlCmd)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
