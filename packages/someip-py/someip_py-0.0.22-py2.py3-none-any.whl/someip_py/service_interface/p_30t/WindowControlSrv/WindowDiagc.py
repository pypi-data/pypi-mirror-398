from someip_py.codec import *


class IdtWinDiagc(SomeIpPayload):

    _include_struct_len = True

    OpenCirc: Uint8

    OverCurrent: Uint8

    IntElecFailr: Uint8

    OverTemperature: Uint8

    MissCal: Uint8

    MeclFailr: Uint8

    RippleFault: Uint8

    VccOutOfRng: Uint8

    def __init__(self):

        self.OpenCirc = Uint8()

        self.OverCurrent = Uint8()

        self.IntElecFailr = Uint8()

        self.OverTemperature = Uint8()

        self.MissCal = Uint8()

        self.MeclFailr = Uint8()

        self.RippleFault = Uint8()

        self.VccOutOfRng = Uint8()


class IdtAllWindowDiagc(SomeIpPayload):

    _include_struct_len = True

    WindowID: Uint8

    WindowDiagc: IdtWinDiagc

    def __init__(self):

        self.WindowID = Uint8()

        self.WindowDiagc = IdtWinDiagc()


class IdtWindowDiagcAry(SomeIpPayload):

    IdtWindowDiagcAry: SomeIpDynamicSizeArray[IdtAllWindowDiagc]

    def __init__(self):

        self.IdtWindowDiagcAry = SomeIpDynamicSizeArray(IdtAllWindowDiagc)
