from someip_py.codec import *


class IdtMirrAdjCmdTrgSrc(SomeIpPayload):

    IdtMirrAdjCmdTrgSrc: Uint8

    def __init__(self):

        self.IdtMirrAdjCmdTrgSrc = Uint8()


class IdtMirrAdjCtlCmd(SomeIpPayload):

    _include_struct_len = True

    MirrID: Uint8

    MirrAdjCmd: Uint8

    def __init__(self):

        self.MirrID = Uint8()

        self.MirrAdjCmd = Uint8()


class IdtMirrAdjCommand(SomeIpPayload):

    IdtMirrAdjCommand: SomeIpDynamicSizeArray[IdtMirrAdjCtlCmd]

    def __init__(self):

        self.IdtMirrAdjCommand = SomeIpDynamicSizeArray(IdtMirrAdjCtlCmd)


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
